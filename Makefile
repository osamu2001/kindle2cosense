# Build target to generate cosense.json from kindle.json
all: build/cosense.json

# Create build directory if it doesn't exist
build:
	mkdir -p build

# Run the python script to generate cosense.json
build/cosense.json: input/kindle.json | build
	python kindle2cosense.py

# Clean up build artifacts
clean:
	rm -f build/cosense.json