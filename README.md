# Adding a New Slave

Slaves are worker nodes that poll the master for album/artist fetch tasks and report results back. Adding a new one takes about 5 minutes.

## Prerequisites

- Docker or Podman installed on the slave machine
- The slave machine needs network access to the master's port (default `8000`)
- The master must have its own `REDIS_HOST` and `MONGO_HOST` configured (slaves don't need direct Redis/MongoDB access — they only communicate with the master via HTTP)

---

## Option 1: Same Docker Compose Stack (Recommended)

If you're running everything via `docker-compose`, just add another `slave-N` service to your `docker-compose.yml`:

```yaml
  slave-3:
    build:
      context: .
      dockerfile: Dockerfile.slave
    depends_on:
      - master
    environment:
      - MASTER_URL=http://master:8000
      - MASTER_API_KEY=changeme      # ← must match your master's MASTER_API_KEY
      - SLAVE_ID=slave-3            # ← unique name for this slave
      - SLAVE_MAX_CLIENTS=5         # ← TLS clients per slave (default 5)
      - BG_SLEEP_MIN=1              # ← min delay before fetching (seconds)
      - BG_SLEEP_MAX=5              # ← max delay before fetching (seconds)
    restart: unless-stopped
```

Then launch it:

```bash
docker compose up -d slave-3
# or
docker compose up -d   # to bring up all services
```

The slave will register itself with the master and appear in the `/admin/slaves` dashboard.

---

## Option 2: Separate Host (Remote Slave)

Build the Docker image on the slave machine:

```bash
# On the slave machine
git clone <your-repo-url>
cd spoti-api
docker build -f Dockerfile.slave -t metabridge-slave:latest .
```

Create a `.env` file for the slave:

```bash
# .env for the slave
MASTER_URL=http://<master-ip>:8000   # IP of the machine running master
MASTER_API_KEY=changeme              # must match the master's MASTER_API_KEY
SLAVE_ID=slave-remote-1             # unique name
SLAVE_MAX_CLIENTS=5                 # TLS clients (keep low, ~3-5 is fine)
BROWSER_PROFILE=chrome_120
AUTO_RETRIES=3
BG_SLEEP_MIN=1
BG_SLEEP_MAX=5
```

Run the container:

```bash
docker run -d \
  --name metabridge-slave \
  --env-file .env \
  --restart unless-stopped \
  metabridge-slave:latest
```

Or with Podman:

```bash
podman run -d \
  --name metabridge-slave \
  --env-file .env \
  --restart unless-stopped \
  localhost/metabridge-slave:latest
```

---

## Option 3: Systemd Service (Bare Metal / VM)

For non-containerized deployment on a Linux server:

```ini
# /etc/systemd/system/metabridge-slave.service

[Unit]
Description=MetaBridge Slave Worker
After=network.target

[Service]
Type=simple
User=samu
WorkingDirectory=/home/samu/spoti-api
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/home/samu/spoti-api/.env
ExecStart=/usr/bin/python3 /home/samu/spoti-api/run_slave.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable metabridge-slave
sudo systemctl start metabridge-slave
```

---

## Key Configuration Values

| Variable | Default | Description |
|---|---|---|
| `MASTER_URL` | `http://localhost:8000` | Full URL to the master server |
| `MASTER_API_KEY` | *(empty)* | Must match the master's `MASTER_API_KEY` |
| `SLAVE_ID` | `slave-<pid>` | Unique identifier shown in the dashboard |
| `SLAVE_MAX_CLIENTS` | `5` | Number of concurrent TLS clients (affects throughput) |
| `BROWSER_PROFILE` | `chrome_120` | Browser fingerprint for Spotify API requests |
| `AUTO_RETRIES` | `3` | Auto-retry failed requests |
| `BG_SLEEP_MIN` | `1` | Min seconds of delay before fetching (per task) |
| `BG_SLEEP_MAX` | `5` | Max seconds of delay before fetching (per task) |

**Tip:** `SLAVE_MAX_CLIENTS` controls parallelism. Each client maintains its own Spotify session. Start with 3-5 and increase if your network can handle it. More clients = faster cache building but higher chance of rate limiting.

---

## Verifying the Slave is Connected

1. Open the master dashboard at `http://<master>:8000/admin/slaves`
2. You should see your new slave listed with a recent heartbeat
3. The queue size should start dropping as slaves pick up tasks
4. Check logs on the slave:

```bash
docker logs -f metabridge-slave
# or
journalctl -u metabridge-slave -f
```

---

## Troubleshooting

**Slave not appearing in dashboard?**
- Check `MASTER_URL` and `MASTER_API_KEY` match the master
- Verify network connectivity: `curl http://<master>:8000/health`
- Check slave logs for auth errors

**Slaves picking up tasks but nothing being saved?**
- Check master logs for `MongoDB upsert` messages
- Verify MongoDB is reachable from the master container

**Too many failed fetches?**
- Reduce `SLAVE_MAX_CLIENTS`
- Increase `BG_SLEEP_MIN` and `BG_SLEEP_MAX` to add more delay between requests
- Check Spotify account token validity if using authenticated sessions
