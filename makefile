runtox:
	. ~/bin/set_proxies; \
	tox test | cat
	coverage html

runflake8:
	flake8 --max-line-length 120 .
