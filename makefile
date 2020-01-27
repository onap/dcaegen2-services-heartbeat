runtox:
	. ~/bin/set_proxies; \
	tox test | cat
	coverage html
