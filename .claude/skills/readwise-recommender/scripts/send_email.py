# /// script
# requires-python = ">=3.11"
# dependencies = ["resend>=2.0.0", "jinja2>=3.0.0"]
# ///

"""Send reading recommendations email via Resend API.

Accepts either:
  --body-file: Pre-rendered HTML file
  --json-file: JSON data to render with embedded template
"""

import argparse
import json
import os

import resend
from jinja2 import Template

# Embedded HTML template - all styling lives here
EMAIL_TEMPLATE = """
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">

<h1 style="color: #1a1a2e; border-bottom: 3px solid #6366f1; padding-bottom: 10px;">📬 Reading Recommendations - {{ date }}</h1>
<p style="color: #666; font-style: italic; margin-bottom: 25px;">{{ context_line }}</p>

<!-- MUST READ SECTION -->
<div style="background: linear-gradient(135deg, #667eea11 0%, #764ba211 100%); border-left: 4px solid #6366f1; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
<h2 style="color: #6366f1; margin-top: 0;">📚 Must Read</h2>
<p style="color: #666; font-style: italic; margin-bottom: 15px;">Quick, high-relevance reads for today</p>
{% for item in must_read %}
<h3 style="color: #1a1a2e; margin-bottom: 5px;">{{ loop.index }}. {{ item.title }}</h3>
<p style="color: #444; line-height: 1.6;"><strong style="color: #6366f1;">Why:</strong> {{ item.why }}</p>
<p style="margin-bottom: 20px;">⏱️ {{ item.time }} · <a href="{{ item.url }}" style="color: #6366f1; font-weight: 600; text-decoration: underline;">Open in Reader →</a></p>
{% endfor %}
</div>

<!-- DEEP DIVE SECTION -->
<div style="background: linear-gradient(135deg, #f093fb11 0%, #f5576c11 100%); border-left: 4px solid #ec4899; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
<h2 style="color: #ec4899; margin-top: 0;">🔬 Deep Dive</h2>
<p style="color: #666; font-style: italic; margin-bottom: 15px;">One significant piece worth your focused attention</p>
<h3 style="color: #1a1a2e; margin-bottom: 5px;">{{ deep_dive.title }}</h3>
<p style="color: #444; line-height: 1.6;"><strong style="color: #ec4899;">Why:</strong> {{ deep_dive.why }}</p>
<p>⏱️ {{ deep_dive.time }} · <a href="{{ deep_dive.url }}" style="color: #ec4899; font-weight: 600; text-decoration: underline;">Open in Reader →</a></p>
</div>

<!-- VIDEO PICK SECTION -->
<div style="background: linear-gradient(135deg, #ff512f11 0%, #f0981911 100%); border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
<h2 style="color: #f59e0b; margin-top: 0;">🎬 Video Pick</h2>
<p style="color: #666; font-style: italic; margin-bottom: 15px;">Today's video recommendation</p>
<h3 style="color: #1a1a2e; margin-bottom: 5px;">{{ video_pick.title }}</h3>
<p style="color: #444; line-height: 1.6;"><strong style="color: #f59e0b;">Why:</strong> {{ video_pick.why }}</p>
<p>🎥 <a href="{{ video_pick.url }}" style="color: #f59e0b; font-weight: 600; text-decoration: underline;">Watch Video →</a></p>
</div>

<!-- INTERESTING CONNECTIONS SECTION -->
<div style="background: linear-gradient(135deg, #11998e11 0%, #38ef7d11 100%); border-left: 4px solid #10b981; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0;">
<h2 style="color: #10b981; margin-top: 0;">🔗 Interesting Connections</h2>
<p style="color: #666; font-style: italic; margin-bottom: 15px;">Unexpected but potentially valuable</p>
{% for item in interesting_connections %}
<h3 style="color: #1a1a2e; margin-bottom: 5px;">{{ loop.index }}. {{ item.title }}</h3>
<p style="color: #444; line-height: 1.6;"><strong style="color: #10b981;">Why:</strong> {{ item.why }}</p>
<p style="margin-bottom: 20px;">⏱️ {{ item.time }} · <a href="{{ item.url }}" style="color: #10b981; font-weight: 600; text-decoration: underline;">Open in Reader →</a></p>
{% endfor %}
</div>

<hr style="border: none; border-top: 1px solid #e5e5e5; margin: 25px 0;">

<!-- LAST WEEK'S READING SECTION -->
<div style="background: #f8f9fa; border-radius: 8px; padding: 15px; margin: 20px 0;">
<h2 style="color: #666; margin-top: 0; font-size: 16px;">📖 Last Week's Reading</h2>
<p style="color: #888; font-size: 13px; margin-bottom: 12px;">You archived {{ last_week.count }} articles this week. Here's what you explored:</p>
<ul style="color: #555; font-size: 13px; line-height: 1.8; margin: 0; padding-left: 20px;">
{% for item in last_week.articles %}
<li><a href="{{ item.url }}" style="color: #555; text-decoration: none;"><strong>{{ item.title }}</strong></a> — {{ item.context }}</li>
{% endfor %}
</ul>
<p style="color: #888; font-size: 12px; margin-top: 12px; margin-bottom: 0;">Keep the momentum going! 🚀</p>
</div>

<p style="color: #888; font-size: 13px; text-align: center;">✅ Archive articles in Readwise after reading to improve future recommendations.</p>

</div>
"""


def render_from_json(json_path: str) -> str:
    """Render HTML from JSON data using embedded template."""
    with open(json_path) as f:
        data = json.load(f)

    template = Template(EMAIL_TEMPLATE)
    return template.render(**data)


def main():
    parser = argparse.ArgumentParser(description="Send reading recommendations email")
    parser.add_argument("--subject", required=True, help="Email subject")

    # Either JSON or pre-rendered HTML
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json-file", help="Path to JSON data file (renders with template)")
    group.add_argument("--body-file", help="Path to pre-rendered HTML file")

    args = parser.parse_args()

    # Get HTML content
    if args.json_file:
        html_body = render_from_json(args.json_file)
        # Also save rendered HTML for reference
        html_path = args.json_file.replace('.json', '.html')
        with open(html_path, 'w') as f:
            f.write(html_body)
        print(f"Rendered HTML saved to: {html_path}")
    else:
        with open(args.body_file) as f:
            html_body = f.read()

    # Send email
    resend.api_key = os.environ["RESEND_API_KEY"]

    sender = os.environ.get("SENDER_EMAIL") or "onboarding@resend.dev"
    if "<" not in sender:
        sender = f"Reading Recommender Agent <{sender}>"

    response = resend.Emails.send({
        "from": sender,
        "to": os.environ["RECIPIENT_EMAIL"],
        "subject": args.subject,
        "html": html_body,
    })

    print(f"Email sent! ID: {response.get('id')}")


if __name__ == "__main__":
    main()
