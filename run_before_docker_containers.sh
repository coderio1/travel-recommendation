#!/bin/bash
# ---------------------------------------------------------------------------
# Create external Docker volumes required by docker-compose.yml.
# ---------------------------------------------------------------------------
for volume in travel_db travel_app; do
    if docker volume inspect "$volume" > /dev/null 2>&1; then
        echo "Volume '$volume' already exists, skipping."
    else
        docker volume create "$volume"
        echo "Volume '$volume' created."
    fi
done