"""HTML report rendering service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from jinja2 import Template

MAX_LOG_LINES = 500

_BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Test Report - {{ task_info.target_name or task_id }}</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 24px; color: #1f2937; }
    .wrap { max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,.08); }
    .header { padding: 24px; background: #0f766e; color: #fff; }
    .section { padding: 20px 24px; border-top: 1px solid #e5e7eb; }
    .stats { display: grid; gap: 12px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .card { background: #f9fafb; border-left: 4px solid #0f766e; padding: 12px; border-radius: 6px; }
    .card h4 { margin: 0; font-size: 12px; color: #6b7280; }
    .card p { margin: 6px 0 0; font-size: 28px; font-weight: 700; }
    .log { background: #f8fafc; border-left: 4px solid #cbd5e1; margin: 8px 0; padding: 10px; border-radius: 6px; }
    .meta { color: #6b7280; font-size: 12px; margin-bottom: 4px; }
    .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
    .shot { border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
    .shot img { width: 100%; display: block; }
    .shot .info { padding: 8px 10px; font-size: 12px; color: #374151; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h1 style="margin:0;">Test Report</h1>
      <div style="margin-top:8px;font-size:13px;opacity:.9;">
        task={{ task_id }} | type={{ task_info.type or '-' }} | started={{ task_info.started_at or '-' }}
      </div>
    </div>

    <div class="section">
      <h2 style="margin:0 0 12px;">Summary</h2>
      <div class="stats">
        <div class="card"><h4>Total</h4><p>{{ statistics.total or 0 }}</p></div>
        <div class="card" style="border-left-color:#16a34a"><h4>Success</h4><p>{{ statistics.success or 0 }}</p></div>
        <div class="card" style="border-left-color:#dc2626"><h4>Failed</h4><p>{{ statistics.failed or 0 }}</p></div>
        <div class="card" style="border-left-color:#64748b"><h4>Skipped</h4><p>{{ statistics.skipped or 0 }}</p></div>
      </div>
    </div>

    {% if screenshots %}
    <div class="section">
      <h2 style="margin:0 0 12px;">Screenshots ({{ screenshots|length }})</h2>
      <div class="grid">
        {% for shot in screenshots %}
        <div class="shot">
          {% if shot.image_src %}<img src="{{ shot.image_src }}" alt="screenshot" />{% endif %}
          <div class="info">{{ shot.step_name or 'unknown step' }} | {{ shot.timestamp or '-' }}</div>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endif %}

    <div class="section">
      <h2 style="margin:0 0 12px;">Logs ({{ logs|length }})</h2>
      {% for log in logs[:max_logs] %}
      <div class="log">
        <div class="meta">{{ log.timestamp or '' }} | {{ log.level or 'INFO' }}</div>
        <div>{{ log.message or '' }}</div>
      </div>
      {% endfor %}
      {% if logs|length > max_logs %}
      <p style="color:#6b7280">... and {{ logs|length - max_logs }} more logs</p>
      {% endif %}
    </div>

    <div class="section" style="font-size:12px;color:#6b7280;">Generated at {{ generation_time }}</div>
  </div>
</body>
</html>
"""


class ReportGenerator:
    """Generate HTML reports for test execution."""

    def generate_html_report(
        self,
        task_id: str,
        task_info: Dict[str, Any],
        logs: List[Dict[str, Any]],
        screenshots: List[Dict[str, Any]],
        statistics: Dict[str, Any],
    ) -> str:
        return self._render_html(
            task_id=task_id,
            task_info=task_info,
            logs=logs,
            screenshots=screenshots,
            statistics=statistics,
            embed_images=False,
        )

    def generate_html_report_with_embedded_images(
        self,
        task_id: str,
        task_info: Dict[str, Any],
        logs: List[Dict[str, Any]],
        screenshots: List[Dict[str, Any]],
        statistics: Dict[str, Any],
    ) -> str:
        return self._render_html(
            task_id=task_id,
            task_info=task_info,
            logs=logs,
            screenshots=screenshots,
            statistics=statistics,
            embed_images=True,
        )

    def _normalize_screenshots(
        self, screenshots: List[Dict[str, Any]], embed_images: bool
    ) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for shot in screenshots:
            item = dict(shot)
            if embed_images and shot.get("base64"):
                item["image_src"] = f"data:image/png;base64,{shot['base64']}"
            else:
                item["image_src"] = shot.get("filepath") or shot.get("url") or ""
            normalized.append(item)
        return normalized

    def _render_html(
        self,
        *,
        task_id: str,
        task_info: Dict[str, Any],
        logs: List[Dict[str, Any]],
        screenshots: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        embed_images: bool,
    ) -> str:
        template = Template(_BASE_TEMPLATE)
        return template.render(
            task_id=task_id,
            task_info=task_info or {},
            logs=logs or [],
            screenshots=self._normalize_screenshots(screenshots or [], embed_images=embed_images),
            statistics=statistics or {},
            max_logs=MAX_LOG_LINES,
            generation_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        )
