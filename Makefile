# Makefile

# Variables
PORT ?= 5001

# Default target
all: build run

# Build Docker image
build:
	docker build -t cot_at_home .

# Run Docker image
run:
	docker run -it -p $(PORT):$(PORT) -e PORT=$(PORT) --env-file .env cot_at_home:latest


.PHONY: all build run