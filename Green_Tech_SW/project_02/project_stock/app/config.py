# 실제투자로 진행할 시 True를 False로 변경
is_paper_trading = True

# 따옴표 안에 작성할 것
real_app_key = "Z7ZqCqvfJzHR4_l9ssyZdVUn73AtngU4ub1r9W3N1r4"
real_app_secret = "lKTXsF8zC-pEhFK8-il0gtxlu4z1bqeeOOb3p1ukhOU"

paper_app_key = "Z7ZqCqvfJzHR4_l9ssyZdVUn73AtngU4ub1r9W3N1r4"
paper_app_secret = "lKTXsF8zC-pEhFK8-il0gtxlu4z1bqeeOOb3p1ukhOU"

real_host_url = "https://api.kiwoom.com"
paper_host_url = "https://mockapi.kiwoom.com"

real_socket_url = "wss://api.kiwoom.com:10000"
paper_socket_url = "wss://mockapi.kiwoom.com:10000"

app_key = paper_app_key if is_paper_trading else real_app_key
app_secret = paper_app_secret if is_paper_trading else real_app_secret
host_url = paper_host_url if is_paper_trading else real_host_url
socket_url = paper_socket_url if is_paper_trading else real_socket_url