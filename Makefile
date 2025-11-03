.PHONY: all package
all package:
	python3 extract_and_package.py

.PHONY: clean
clean:
	rm -rf installer installer_payload.zip *.deb
