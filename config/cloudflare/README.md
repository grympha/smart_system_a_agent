# Cloudflare Named Tunnel

Copy `tunnel.yml.example` to `tunnel.yml`, then replace:

- `YOUR_TUNNEL_ID`
- `YOUR_USER`
- `agent.my-domain.com`

The tunnel should point to the local Flask app:

```text
http://127.0.0.1:5000
```

Set the same public hostname in `.env`:

```text
PUBLIC_BASE_URL=https://agent.my-domain.com
```
