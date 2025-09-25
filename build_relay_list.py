#!/usr/bin/env python3
"""CLI for building Mullvad SOCKS5 relay lists."""

from __future__ import annotations

import argparse
import json
import datetime as dt
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Set

from mullvad.api import MullvadAPI
from mullvad.errors import RelayBuildError
from mullvad.output import write_json, write_text, write_pac
from mullvad.enrich import enrich_relays
from mullvad.pipeline import PipelineStats, SourceManager, SourceResult
from mullvad.transform import (
    FilterConfig,
    SourcePayload,
    build_relays,
    filter_relays,
    format_filter_diagnostics,
)
from mullvad.validation import validate_relays
from mullvad.verifier import (
    preflight_targets,
    run_mubeng,
    run_proxy_verification,
)
from mullvad.proxy_checker import ProxyScraperChecker
from scripts.verify_proxies import HTTP_TEST_URL, WS_TEST_URL

SLA_SECONDS = 5.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--countries",
        nargs="*",
        help="Country names, ISO codes, or location IDs to include",
    )
    parser.add_argument(
        "--cities",
        nargs="*",
        help="City names or location IDs to include",
    )
    parser.add_argument(
        "--include-owned",
        action="store_true",
        help="Include Mullvad owned relays in the output (excluded by default)",
    )
    parser.add_argument(
        "--providers-allow",
        help="Comma-separated list of provider names to allow exclusively",
    )
    parser.add_argument(
        "--providers-block",
        help="Comma-separated list of provider names to exclude",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit the number of relays in the output after filtering",
    )
    parser.add_argument(
        "--output-dir",
        default="build",
        help="Directory to write artifact files into (default: build)",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=300,
        help="Cache TTL for API responses in seconds (default: 300)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass on-disk cache and fetch fresh data",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress information",
    )
    parser.add_argument(
        "--enable-proxy-checker",
        action="store_true",
        help="Use Proxy Scraper Checker metadata enricher",
    )
    parser.add_argument(
        "--proxy-checker-bin",
        default="proxy-scraper-checker",
        help="Path or name of the Proxy Scraper Checker binary",
    )
    parser.add_argument(
        "--proxy-checker-arg",
        action="append",
        default=[],
        help="Additional argument passed to Proxy Scraper Checker (repeatable)",
    )
    parser.add_argument(
        "--proxy-checker-timeout",
        type=int,
        default=60,
        help="Timeout in seconds for Proxy Scraper Checker",
    )
    parser.add_argument(
        "--proxy-checker-export",
        type=Path,
        help="Optional path to pre-generated Proxy Scraper Checker JSON export",
    )
    parser.add_argument(
        "--verify-limit",
        type=int,
        default=0,
        help="Number of relays to probe via Binance targets (0 disables)",
    )
    parser.add_argument(
        "--verify-timeout",
        type=int,
        default=8,
        help="Timeout in seconds for verification probes (default: 8)",
    )
    parser.add_argument(
        "--verify-http-url",
        default=HTTP_TEST_URL,
        help="HTTP(S) URL to use for verification probes",
    )
    parser.add_argument(
        "--verify-ws-url",
        default=WS_TEST_URL,
        help="WebSocket URL to use for verification probes",
    )
    parser.add_argument(
        "--verify-http-ca",
        type=Path,
        help="CA bundle to trust for HTTP verification",
    )
    parser.add_argument(
        "--verify-http-insecure",
        action="store_true",
        help="Disable TLS verification for HTTP probes",
    )
    parser.add_argument(
        "--verify-mubeng",
        action="store_true",
        help="Run Mubeng-style summary based on verification results",
    )
    parser.add_argument(
        "--mubeng-bin",
        default="mubeng",
        help="Path or name of the Mubeng binary used for verification",
    )
    parser.add_argument(
        "--mubeng-arg",
        action="append",
        default=[],
        help="Additional argument passed to the Mubeng binary (repeatable)",
    )
    parser.add_argument(
        "--mubeng-timeout",
        type=int,
        default=60,
        help="Timeout in seconds for Mubeng verification",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Append a JSON summary for each run to this file",
    )
    parser.add_argument(
        "--emit-canonical-json",
        action="store_true",
        help="Write a Mullvad canonical JSON artifact without enrichment",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    def log(message: str) -> None:
        if args.verbose:
            timestamp = dt.datetime.now().isoformat(timespec="seconds")
            print(f"[{timestamp}] {message}")

    cache_dir = Path(".cache")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.no_cache:
        cache_dir.mkdir(parents=True, exist_ok=True)

    api_client = MullvadAPI(
        cache_dir=cache_dir,
        ttl_seconds=args.cache_ttl,
        use_cache=not args.no_cache,
    )

    source_manager = SourceManager(api_client=api_client)
    stats = PipelineStats(sla_seconds=SLA_SECONDS)
    summary_payload: dict[str, object] = {
        "started_at": stats.started_at.isoformat(),
        "success": False,
        "sources": [],
        "relays": {},
        "notes": stats.notes,
    }

    verification_summary_data: dict[str, object] | None = None
    mubeng_report: dict | None = None

    json_path = output_dir / "mullvad_relays.json"
    text_path = output_dir / "mullvad_relays.txt"
    pac_path = output_dir / "mullvad_relays.pac"
    canonical_path = (
        output_dir / "mullvad_relays_canonical.json"
        if args.emit_canonical_json
        else None
    )

    proxy_checker_args = [str(value) for value in args.proxy_checker_arg]
    mubeng_args = [str(value) for value in args.mubeng_arg]

    try:
        log("Fetching relay sources")
        with stats.stage("fetch"):
            source_results = source_manager.fetch_all(force_refresh=args.no_cache)
        stats.record_source_results(source_results)
        summary_payload["sources"] = _summarize_sources(source_results)

        source_payloads: list[SourcePayload] = []
        for result in source_results:
            if result.error:
                message = (
                    f"Failed to fetch {result.name}: {result.error}"
                    if args.verbose
                    else f"Failed to fetch {result.name}"
                )
                print(message, file=sys.stderr)
                if result.name == "mullvad":
                    raise RelayBuildError("Unable to fetch Mullvad relay data") from result.error
                continue
            if result.payload is not None:
                source_payloads.append(
                    SourcePayload(name=result.name, payload=result.payload)
                )

        if not source_payloads:
            raise RelayBuildError("No relay sources were retrieved successfully")

        log("Transforming relays")
        with stats.stage("transform"):
            relays = build_relays(source_payloads)

        relays_summary = summary_payload.setdefault("relays", {})  # type: ignore[assignment]
        relays_summary["fetched"] = len(relays)

        config = FilterConfig(
            countries=_list_to_set(args.countries),
            cities=_list_to_set(args.cities),
            include_owned=args.include_owned,
            providers_allow=_csv_to_set(args.providers_allow),
            providers_block=_csv_to_set(args.providers_block),
            limit=args.limit,
        )

        with stats.stage("filter"):
            filtered, report = filter_relays(relays, config)

        relays_summary["filtered"] = len(filtered)
        relays_summary["unmatched_filters"] = report.unmatched_filters
        relays_summary["excluded_samples"] = [
            {
                "reason": sample.reason,
                "endpoint": sample.relay.socks5_endpoint,
            }
            for sample in report.excluded_samples
        ]

        if args.verbose:
            message, sample_lines = format_filter_diagnostics(
                report,
                remaining_count=len(filtered),
                limit=3,
            )
            if message:
                log(message)
            for line in sample_lines:
                log(line)

        with stats.stage("validate"):
            validation = validate_relays(filtered)

        relays_summary["validated"] = len(validation.valid_relays)
        if validation.issues:
            relays_summary["validation_issues"] = [
                {
                    "endpoint": issue.relay.socks5_endpoint,
                    "reason": issue.reason,
                }
                for issue in validation.issues
            ]

        if args.verbose:
            log(
                "Validation summary: "
                f"{len(validation.valid_relays)} valid, {len(validation.issues)} rejected"
            )
            for issue in validation.issues[:3]:
                relay = issue.relay
                log(
                    "Validation issue: "
                    f"{relay.socks5_endpoint} -> {issue.reason}"
                )

        valid_relays = validation.valid_relays

        verification_required = args.verify_limit > 0 or args.verify_mubeng
        verification_sample_size: Optional[int]
        if args.verify_limit and args.verify_limit > 0:
            verification_sample_size = args.verify_limit
        else:
            verification_sample_size = None

        proxy_checker = None
        if args.enable_proxy_checker:
            export_path = args.proxy_checker_export
            if export_path is not None and not export_path.exists():
                raise RelayBuildError(
                    "Proxy Scraper Checker export not found. Provide a valid path or run the checker binary."
                )
            proxy_checker = ProxyScraperChecker(
                binary=str(args.proxy_checker_bin),
                args=proxy_checker_args,
                timeout=args.proxy_checker_timeout,
                export_path=export_path,
            )

        with stats.stage("enrich"):
            enrichment = enrich_relays(
                valid_relays,
                verification_sample_size=verification_sample_size,
                proxy_checker=proxy_checker,
            )
        enriched_relays = enrichment.enriched_relays
        relays_summary["enriched"] = len(enriched_relays)
        if enrichment.checker_summary is not None:
            relays_summary["checker_summary"] = enrichment.checker_summary
        verification_candidates = enrichment.verification_candidates

        if args.enable_proxy_checker and args.verbose:
            if enrichment.checker_summary:
                log(f"Proxy checker summary: {enrichment.checker_summary}")
            else:
                log("Proxy checker did not provide summary metadata")

        if verification_required:
            endpoints = [relay.socks5_endpoint for relay in verification_candidates]
            if args.verify_limit and args.verify_limit > 0:
                endpoints = endpoints[: args.verify_limit]
            if not endpoints:
                raise RelayBuildError("Verification requested but no relay candidates available")

            http_verify_option = _resolve_http_verify(args)
            preflight_targets(
                args.verify_http_url,
                args.verify_ws_url,
                timeout=args.verify_timeout,
                http_verify=http_verify_option,
            )

            with stats.stage("verify"):
                summary = run_proxy_verification(
                    endpoints,
                    timeout=args.verify_timeout,
                    http_url=args.verify_http_url,
                    ws_url=args.verify_ws_url,
                    http_verify=http_verify_option,
                )

            verification_summary_data = {
                "total": summary.total,
                "http_success": summary.http_success,
                "ws_success": summary.ws_success,
                "results": [
                    {
                        "endpoint": result.endpoint,
                        "http_ok": result.http_ok,
                        "http_error": result.http_error,
                        "http_origin": result.http_origin,
                        "ws_ok": result.ws_ok,
                        "ws_error": result.ws_error,
                    }
                    for result in summary.results
                ],
            }
            summary_payload["verification"] = verification_summary_data

            if args.verbose:
                log(
                    "Verification summary: "
                    f"HTTP {summary.http_success}/{summary.total}, "
                    f"WS {summary.ws_success}/{summary.total}"
                )

            if summary.failures:
                failed = ", ".join(result.endpoint for result in summary.failures)
                raise RelayBuildError(f"Proxy verification failed for: {failed}")

            if args.verify_mubeng:
                with stats.stage("mubeng"):
                    mubeng_report = run_mubeng(
                        endpoints,
                        binary=str(args.mubeng_bin),
                        args=mubeng_args,
                        timeout=args.mubeng_timeout,
                    )
                summary_payload["mubeng"] = mubeng_report
                if args.verbose:
                    log(f"Mubeng summary: {mubeng_report}")
                if not mubeng_report.get("ok", True):
                    raise RelayBuildError("Mubeng verification reported failures")

        if not enriched_relays:
            print("No relays matched the provided filters", file=sys.stderr)
            return 1

        with stats.stage("output"):
            log(f"Writing JSON to {json_path}")
            write_json([entry.to_dict() for entry in enriched_relays], json_path)

            log(f"Writing text list to {text_path}")
            write_text([entry.relay for entry in enriched_relays], text_path)

            log(f"Writing PAC script to {pac_path}")
            write_pac([entry.relay for entry in enriched_relays], pac_path)

            if canonical_path is not None:
                log(f"Writing canonical JSON to {canonical_path}")
                write_json(valid_relays, canonical_path)

        relays_summary["written"] = len(enriched_relays)
        artifacts_payload = {
            "json": str(json_path),
            "text": str(text_path),
            "pac": str(pac_path),
            "count": len(enriched_relays),
        }
        if canonical_path is not None:
            artifacts_payload["canonical"] = str(canonical_path)

        summary_payload["artifacts"] = artifacts_payload

        stats.finish()

        if stats.sla_breached:
            warning = (
                f"Pipeline runtime exceeded SLA of {SLA_SECONDS:.1f}s: "
                f"total {stats.total_duration:.2f}s"
            )
            print(warning, file=sys.stderr)
            stats.add_note(warning)

        if args.verbose:
            for measurement in stats.stages:
                log(f"Stage {measurement.name} completed in {measurement.duration:.3f}s")

        summary_payload["success"] = True

        print(
            f"Wrote {len(enriched_relays)} relays to {json_path}, {text_path}, and {pac_path}"
        )
        return 0
    except RelayBuildError as exc:
        summary_payload["error"] = str(exc)
        raise
    finally:
        stats.finish()
        summary_payload["finished_at"] = (
            stats.finished_at.isoformat() if stats.finished_at else None
        )
        summary_payload["duration_seconds"] = stats.total_duration
        summary_payload["sla_breached"] = stats.sla_breached
        summary_payload["stages"] = [
            {"name": measurement.name, "duration": measurement.duration}
            for measurement in stats.stages
        ]
        summary_payload["notes"] = stats.notes
        if not summary_payload.get("sources") and stats.source_results:
            summary_payload["sources"] = _summarize_sources(stats.source_results)
        if args.log_file is not None:
            _append_log(args.log_file, summary_payload)


def _list_to_set(values: Optional[Sequence[str]]) -> Optional[Set[str]]:
    if not values:
        return None
    return {value.strip().lower() for value in values if value.strip()}


def _csv_to_set(value: Optional[str]) -> Optional[Set[str]]:
    if not value:
        return None
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _resolve_http_verify(args: argparse.Namespace) -> bool | str:
    if args.verify_http_insecure:
        return False
    if args.verify_http_ca is not None:
        return str(args.verify_http_ca)
    return True


def _summarize_sources(results: Sequence[SourceResult]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for result in results:
        entry: dict[str, object] = {
            "name": result.name,
            "success": result.error is None,
            "duration": result.duration,
            "attempts": result.attempts,
            "cache_bypassed": result.cache_bypassed,
        }
        if result.error is not None:
            entry["error"] = str(result.error)
        summary.append(entry)
    return summary


def _append_log(path: Path, payload: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        pass
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"Failed to write log file {path}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RelayBuildError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    except KeyboardInterrupt:  # pragma: no cover - CLI convenience
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
