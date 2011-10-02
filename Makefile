all:	docstrings.i

clean:
	rm -rf xml docstrings.i

xml/index.xml:
	doxygen doxygen.conf

docstrings.i:	xml/index.xml
	python external/doxy2swig.py $^ $@
