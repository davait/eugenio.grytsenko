all:
	@echo "> make init"

init:
	# rm -f admin1CodesASCII.txt AR.zip AR.txt
	rm -f garage_sale.db
	rm -rf uploads && mkdir uploads
	python create_tables.py
	python load_geonames_locations.py
	python init_db.py
	python seed_data.py
	python fix_faiss_embeddings.py
	# python featured_batch.py
