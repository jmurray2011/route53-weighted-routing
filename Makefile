# Include environment variables from .env file
include .env
export $(shell sed 's/=.*//' .env)

# Define variables
ZIP_FILE=lambda_handler.zip

# Default target executed when no arguments are given to make
all: deploy

# Target for zipping the lambda function
zip:
	@echo "Zipping the Python script..."
	zip $(ZIP_FILE) $(SOURCE_FILE)

# Target for deploying to AWS Lambda
deploy: zip
	@echo "Deploying to AWS Lambda using profile $(AWS_PROFILE) in region $(AWS_REGION)..."
	aws lambda update-function-code --function-name $(FUNCTION_NAME) --zip-file fileb://$(ZIP_FILE) --profile $(AWS_PROFILE) --region $(AWS_REGION)

# Clean up the zip file
clean:
	rm -f $(ZIP_FILE)

.PHONY: all zip deploy clean
