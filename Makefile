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
	@echo "Autentique o sudo (será cacheado para os próximos comandos):"
	@sudo -v
	@echo "Recuperando IP do container..."
	$(eval IP := $(shell docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' textgrader_tool-flask-app-1))
	@echo "IP encontrado: $(IP)"
	@sudo sed -i 's|proxy_pass http://[0-9.]\+:5000/;|proxy_pass http://$(IP):5000/;|' /etc/nginx/sites-available/aquarii.conf
	@sudo service nginx restart
	@echo "✓ Nginx atualizado com IP $(IP) e reiniciado"

restart: down up
	sleep 10
	$(MAKE) update-nginx-proxy