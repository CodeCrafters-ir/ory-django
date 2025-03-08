docker compose exec hydra \
  hydra create client \
  --endpoint http://localhost:4445 \
  --grant-type authorization_code,refresh_token \
  --response-type code,id_token \
  --scope openid,offline \
  --redirect-uri http://localhost:3000/callback
