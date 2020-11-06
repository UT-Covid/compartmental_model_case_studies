all: app

app-assets:
	cp -R ../inputs assets/
	cp -R ../data assets/
	cp -R ../src assets/
	cp ../requirements.txt assets/
	rm -rf assets/src/SEIRcity/configs/*configs
	rm -rf "assets/data/Austin Data"
	rm -rf "assets/data/Excel Data"
	find assets -path *__pycache__ -type d -print0 | xargs -0 /bin/rm -rf

app-prepare:
	cd assets ; zip -qrT static.zip data inputs src; rm -rf inputs; rm -rf src; rm -rf data

app.json: app-assets
	cd assets ; python -B -m src.SEIRcity.cli app > ../app.json

clean:
	find . -type d -name __pycache__ -exec rm -r {} \+
	rm -f app.json
	rm -rf assets/src
	rm -rf assets/data
	rm -rf assets/inputs
	rm -f assets/requirements.txt
	rm -rf assets/static.zip

app: clean app.json app-prepare
	cp ../requirements.txt assets/
	tapis apps deploy
