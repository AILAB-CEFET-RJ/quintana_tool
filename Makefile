COMPOSE_FILE := docker-compose.yml
DOCKER_COMPOSE := docker compose

setup-env:
	cp .env.example .env

up:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up --build -d

down:
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down --remove-orphans

remove-logs:
	cd backend/src && sudo rm -r *_log.txt

update-nginx-proxy:
	@echo "Autentique o sudo:"
	@sudo -v
	sudo sed -i 's|proxy_pass http://[0-9.]\+:5000/;|proxy_pass http://127.0.0.1:5000/;|' /etc/nginx/sites-available/aquarii.conf
	@sudo service nginx restart
	@echo "✓ Nginx reiniciado"

restart: down up
	@for i in 1 2 3 4 5; do \
		echo "Aguardando... $$i/5 minutos"; \
		sleep 60; \
	done
	$(MAKE) update-nginx-proxy
