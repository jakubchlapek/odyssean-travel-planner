#!/bin/bash
# Wait for the database to be ready // function from wait-for-it.sh by vishnubob
./wait-for-it.sh db:3306 --timeout=30 --strict -- echo "Database is up"

# Run the Flask migration
while true; do
    flask db upgrade
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Upgrade command failed, retrying in 5 secs...
    sleep 5
done
echo "Flask migration successful!"

echo "Seeding the database..."
flask seed
echo "Updating the exchange rates..."
flask update_exchange_rates
echo "Starting Flask application..."
flask run