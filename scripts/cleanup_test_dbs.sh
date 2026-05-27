#!/usr/bin/env bash

set -euo pipefail

MYSQL_CONTAINER="${MYSQL_CONTAINER:-mysql8}"
MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"
PRESERVE_DB="${PRESERVE_DB:-fishradar_feature_time_test}"

usage() {
  cat <<'EOF'
用法:
  bash scripts/cleanup_test_dbs.sh

可选环境变量:
  MYSQL_CONTAINER  默认 mysql8
  MYSQL_HOST       默认 127.0.0.1
  MYSQL_PORT       默认 3306
  MYSQL_USER       默认 root
  MYSQL_PASSWORD   默认 123456
  PRESERVE_DB      默认 fishradar_feature_time_test

说明:
  - 会删除所有名称以 fishradar 开头、且不等于 PRESERVE_DB 的数据库
  - 优先使用本机 mysql 客户端
  - 若本机无 mysql，则回退到 docker exec <MYSQL_CONTAINER> mysql
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mysql_query() {
  local sql="$1"
  if command -v mysql >/dev/null 2>&1; then
    MYSQL_PWD="$MYSQL_PASSWORD" mysql \
      -h "$MYSQL_HOST" \
      -P "$MYSQL_PORT" \
      -u "$MYSQL_USER" \
      -N \
      -e "$sql"
    return
  fi

  if docker ps --format '{{.Names}}' | grep -Fxq "$MYSQL_CONTAINER"; then
    docker exec "$MYSQL_CONTAINER" mysql \
      -u"$MYSQL_USER" \
      -p"$MYSQL_PASSWORD" \
      -N \
      -e "$sql"
    return
  fi

  echo "未找到可用的 mysql 客户端，也没有运行中的容器 $MYSQL_CONTAINER" >&2
  exit 1
}

databases=()
while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  databases+=("$line")
done < <(mysql_query "SHOW DATABASES LIKE 'fishradar%';")

if [[ "${#databases[@]}" -eq 0 ]]; then
  echo "没有发现 fishradar 相关数据库。"
  exit 0
fi

to_drop=()
for db in "${databases[@]}"; do
  if [[ "$db" == "$PRESERVE_DB" ]]; then
    continue
  fi
  to_drop+=("$db")
done

if [[ "${#to_drop[@]}" -eq 0 ]]; then
  echo "没有需要清理的测试库。当前保留: $PRESERVE_DB"
  exit 0
fi

echo "将保留数据库: $PRESERVE_DB"
echo "将删除以下数据库:"
printf '  %s\n' "${to_drop[@]}"

for db in "${to_drop[@]}"; do
  mysql_query "DROP DATABASE IF EXISTS \`$db\`;"
done

echo "清理完成，共删除 ${#to_drop[@]} 个数据库。"
