test:
	@echo Preparing to run tests for the "rest" app...
	@python olistphone/manage.py test rest
run:
	@echo Running server at localhost:8000
	@python olistphone/manage.py runserver
migrate:
	@echo Creating necessary migrations...
	@python olistphone/manage.py makemigrations
	@echo Applying migrations...
	@python olistphone/manage.py migrate
shell:
	@echo Opening Django shell...
	@python olistphone/manage.py shell
