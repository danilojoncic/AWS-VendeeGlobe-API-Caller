# AWS-VendeeGlobe-API-Caller
AWS Lambda function writing to a S3 bucket to keep track of Vendee Globe competitors data, fetches from an unofficial api to get all sailors data, then parses it and extracts the sailors cordinates which are used to fetch accurate weather information for that position from the OpenMeteo API, then it combines the weather with the sailor. 1 fetch for sailors, 1 fetch for weather for all ~30 sailors, every 4 hours every day

Uses the following: S3 bucket, AWS Lambda function, EventBridge schedule to trigger the function to run 5 minutes after the official API gets updated with all the tracking, heading, and wind data

![image](https://github.com/user-attachments/assets/710e504b-c615-4909-bbf7-64a8f15925ff)

