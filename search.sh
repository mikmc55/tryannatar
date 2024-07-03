#!/bin/bash
set -ueo pipefail

CACHE_BUST_KEY=${CACHE_BUST_KEY:-}
SERVER_URL=${SERVER_URL:-http://127.0.0.1:8000}
kind=${1:-}
term=${2:-}
provider=${3:-premiumize}
max_results=10

if [ -z "${kind}" ] || [ -z "${term}" ]; then
	echo "Usage: $0 <kind> <term> [provider]"
	exit 1
fi

if [ "${provider}" == "real_debrid" ]; then
	debrid_api_key=$(op read "op://Personal/Real-debrid/API Token")
elif [ "${provider}" == "premiumize" ]; then
	debrid_api_key=$(op read "op://Personal/Premiumize.me/API Key")
eru/offcloud-support
elif [ "${provider}" == "offcloud" ]; then
	debrid_api_key=$(op read "op://Personal/be4eoumuvxgrf64iuc5a2ap6r4/API Key")
elif [ "${provider}" == "debridlink" ]; then
	debrid_api_key=$(op read "op://Personal/sbu7y6nvqvcx3inmrodr6436ce/credential")
elif [ "${provider}" == "alldebrid" ]; then
	debrid_api_key=$(op read "op://Personal/cesntgi2zvhhiek4dkqbojr47u/Stremio API Key")
else
	echo "Invalid provider: ${provider}"
	exit 1
fi

config=$(cat <<-EOF | jq -c . | base64 -w0
{
	"debrid_service": "${provider}",
	"debrid_api_key": "${debrid_api_key}",
	"max_results": ${max_results},
	"filters": ["yts"]
}

EOF
)

echo "${term}" \
	| tr ',' '\n' \
	| xargs -I{} -P17 \
		timeout 30 curl \
			-H "x-cache-bust: ${CACHE_BUST_KEY}" \
			-SLs \
			-D /dev/stderr \
			-X GET \
			"${SERVER_URL}/${config}/stream/${kind}/{}.json" | jq .
