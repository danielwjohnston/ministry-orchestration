import os
import sys
import html
import urllib.parse
import secrets
import time
from collections import defaultdict
from wsgiref.simple_server import make_server
import database

CSRF_TOKEN = secrets.token_hex(32)
MAX_CONTENT_LENGTH = 1024 * 1024 
rate_limit_records = defaultdict(list)

def is_rate_limited(ip):
    now = time.time()
    rate_limit_records[ip] = [req_time for req_time in rate_limit_records[ip] if now - req_time < 1.0]
    if len(rate_limit_records[ip]) >= 10:
        return True
    rate_limit_records[ip].append(now)
    return False

def render_network_template():
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'network.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    template = template.replace("{{ csrf_token }}", CSRF_TOKEN)
    
    orgs = database.get_all_organizations()
    org_html = ""
    if not orgs:
        org_html = "<li>No organizations in network yet.</li>"
    else:
        for o in orgs:
            name = html.escape(o['name'])
            org_html += f"<li><strong>{name}</strong> <a href=\"/?org_id={o['id']}\" class=\"btn\">Dashboard</a></li>"
    template = template.replace("{{ organizations_list }}", org_html)
    
    pairings = database.get_orchestration_matches()
    pair_html = ""
    if not pairings:
        pair_html = "<p style='color: var(--text-muted);'>No current matches found in the network.</p>"
    else:
        for p in pairings:
            cat = html.escape(p['shared_category'])
            org_need = html.escape(p['need_org_name'])
            org_cap = html.escape(p['cap_org_name'])
            desc_need = html.escape(p['need_description'] or '')
            desc_cap = html.escape(p['cap_description'] or '')
            pair_html += f"""
            <div class="pairing-match">
                <strong>Match Identified: {cat}</strong><br>
                <em>{org_need}</em> needs this: {desc_need}<br>
                <em>{org_cap}</em> can provide this: {desc_cap}
            </div>
            """
    template = template.replace("{{ pairings_list }}", pair_html)
    return template.encode('utf-8')

def render_dashboard_template(org, ministries=None, capabilities=None, needs=None, message=None, message_type=""):
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'dashboard.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    safe_name = html.escape(org['name'] or '') if org else ''
    safe_address = html.escape(org['address'] or '') if org else ''
    safe_contact = html.escape(org['primary_contact'] or '') if org else ''
    safe_message = html.escape(message) if message else ""

    template = template.replace("{{ org['name'] }}", safe_name)
    template = template.replace("{{ org['address'] or '' }}", safe_address)
    template = template.replace("{{ org['primary_contact'] or '' }}", safe_contact)
    template = template.replace("{{ csrf_token }}", CSRF_TOKEN)
    template = template.replace("{{ org['id'] }}", str(org['id']) if org else "")
    
    if message:
        template = template.replace("{% if message %}", "")
        template = template.replace("{% endif %}", "")
        template = template.replace("{{ message_type }}", message_type)
        template = template.replace("{{ message }}", safe_message)
    else:
        import re
        template = re.sub(r'\{% if message %\}.*?\{% endif %\}', '', template, flags=re.DOTALL)

    def render_list(items, template_block):
        if not items:
            return f"<li>No {template_block} recorded yet.</li>"
        html_out = ""
        for item in items:
            name_val = html.escape(item[2] or '')
            desc_val = html.escape(item[3] or '')
            html_out += f"<li><strong>{name_val}</strong> - {desc_val}</li>"
        return html_out

    template = template.replace("{{ ministries_list }}", render_list(ministries, "ministries"))
    template = template.replace("{{ capabilities_list }}", render_list(capabilities, "capabilities"))
    template = template.replace("{{ needs_list }}", render_list(needs, "needs"))
    return template.encode('utf-8')

def get_org_data(org_id):
    org = database.get_organization(org_id)
    if not org:
        return None, [], [], []
    return org, database.get_ministries(org_id), database.get_capabilities(org_id), database.get_needs(org_id)

def application(environ, start_response):
    client_ip = environ.get('REMOTE_ADDR', '127.0.0.1')
    headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Security-Policy', "default-src 'self'; style-src 'unsafe-inline';"),
        ('X-Content-Type-Options', 'nosniff'),
        ('X-Frame-Options', 'DENY'),
        ('Cache-Control', 'no-store')
    ]

    if is_rate_limited(client_ip):
        start_response('429 Too Many Requests', headers)
        return [b"429 Too Many Requests"]
    
    host = environ.get('HTTP_HOST', '')
    if host not in ('127.0.0.1:5050', 'localhost:5050'):
        start_response('403 Forbidden', [('Content-Type', 'text/plain')])
        return [b"403 Forbidden: Invalid Host header"]

    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')
    qs = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''))

    if path != '/':
        start_response('404 Not Found', headers)
        return [b"Not Found"]

    if method == 'GET':
        if 'org_id' in qs:
            org_id = int(qs['org_id'][0])
            org, ministries, capabilities, needs = get_org_data(org_id)
            if not org:
                start_response('404 Not Found', headers)
                return [b"Organization Not Found"]
            response_body = render_dashboard_template(org, ministries, capabilities, needs)
        else:
            response_body = render_network_template()
        
        start_response('200 OK', headers)
        return [response_body]

    elif method == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0

        if request_body_size > MAX_CONTENT_LENGTH:
            start_response('413 Payload Too Large', headers)
            return [b"Payload Too Large"]

        request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')
        parsed_body = urllib.parse.parse_qs(request_body)
        submitted_token = parsed_body.get('csrf_token', [''])[0]
        
        if not secrets.compare_digest(submitted_token, CSRF_TOKEN):
            # If we were on an org dashboard, render it with error
            if 'org_id' in parsed_body:
                org, ministries, capabilities, needs = get_org_data(int(parsed_body['org_id'][0]))
                response_body = render_dashboard_template(org, ministries, capabilities, needs, "Invalid session token.", "error")
            else:
                response_body = render_network_template() # Too simple for this MVP to handle error rendering on network page
            start_response('403 Forbidden', headers)
            return [response_body]

        action = parsed_body.get('action', [''])[0]
        
        if action == 'create_org':
            name = parsed_body.get('name', [''])[0].strip()
            if name:
                new_id = database.create_organization(name)
                # Redirect to new dashboard
                headers.append(('Location', f'/?org_id={new_id}'))
                start_response('303 See Other', headers)
                return [b""]
            else:
                start_response('400 Bad Request', headers)
                return [b"Name required"]

        # All other actions require an org_id
        org_id_str = parsed_body.get('org_id', [''])[0]
        if not org_id_str:
            start_response('400 Bad Request', headers)
            return [b"org_id required"]
        org_id = int(org_id_str)
        
        msg = "Action completed."
        msg_type = "success"

        if action == 'update_org':
            name = parsed_body.get('name', [''])[0].strip()
            address = parsed_body.get('address', [''])[0].strip()
            primary_contact = parsed_body.get('primary_contact', [''])[0].strip()
            if not name:
                msg = "Organization Name is required."
                msg_type = "error"
            else:
                database.update_organization(org_id, name, address, primary_contact)
                msg = "Profile saved securely."
        
        elif action == 'add_ministry':
            name = parsed_body.get('name', [''])[0].strip()
            desc = parsed_body.get('description', [''])[0].strip()
            if name:
                database.add_ministry(org_id, name, desc)
                msg = "Ministry added."
        
        elif action == 'add_capability':
            cat = parsed_body.get('category', [''])[0].strip()
            desc = parsed_body.get('description', [''])[0].strip()
            if cat:
                database.add_capability(org_id, cat, desc)
                msg = "Capability added."
        
        elif action == 'add_need':
            cat = parsed_body.get('category', [''])[0].strip()
            desc = parsed_body.get('description', [''])[0].strip()
            if cat:
                database.add_need(org_id, cat, desc)
                msg = "Need added."

        org, ministries, capabilities, needs = get_org_data(org_id)
        response_body = render_dashboard_template(org, ministries, capabilities, needs, msg, msg_type)
        start_response('200 OK', headers)
        return [response_body]

    else:
        start_response('405 Method Not Allowed', headers)
        return [b"Method Not Allowed"]

if __name__ == '__main__':
    database.init_db()
    host = '127.0.0.1'
    port = 5050
    with make_server(host, port, application) as httpd:
        print(f"Secure Ministry Orchestration MVP running locally at http://{host}:{port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)
