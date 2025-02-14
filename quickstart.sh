client=$(docker compose -f quickstart.yml exec hydra \
    hydra create client \
    --endpoint http://127.0.0.1:4445/ \
    --format json \
    --grant-type client_credentials)

client_id=$(echo $client | jq -r '.client_id')
client_secret=$(echo $client | jq -r '.client_secret')

docker compose -f quickstart.yml exec hydra \
  hydra perform client-credentials \
  --endpoint http://127.0.0.1:4444/ \
  --client-id "$client_id" \
  --client-secret "$client_secret"