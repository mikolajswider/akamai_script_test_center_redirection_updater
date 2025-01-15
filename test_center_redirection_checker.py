import pandas as pd
import requests
import argparse
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from urllib.parse import urljoin
import json
import numpy

# Edgegrid 
edgerc = EdgeRc('~/.edgerc')
section = 'default'
baseurl = 'https://%s' % edgerc.get(section, 'host')

# API_CALL1: Define the API call function to get the Test Suite ID 

def make_api_call_1(test_suite_name):
    #Test Suite ID
    test_suite_id = -1

    # Define the API http request
    http_request = requests.Session()
    http_request.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    
    path = "/test-management/v3/functional/test-suites"
    headers = {}
    headers["accept"]="application/json"
    http_request.headers = headers

    # Perform the API_CALL_1
    try:
        http_response = http_request.get(urljoin(baseurl, path))
        http_response.raise_for_status()  # Raise an error for HTTP error responses
        #http_status_code= http_response.status_code
        #print(http_status_code)
        #return http_response.json()  # Assuming the API returns JSON
        test_suites_list = json.loads(http_response.text)["testSuites"]
        http_response.close()
        for item in test_suites_list:
            if test_suite_name == item["testSuiteName"]:
                test_suite_id = item["testSuiteId"]
        return(test_suite_id)
    except requests.exceptions.RequestException as e:
        print(f"ERROR - API_CALL_1 failed: {e}")
        return None

# API_CALL2: Define the API call function to update a Test Suite with a new Test Case
def make_api_call_2(source_url, destination_url, status_code, geo_redirect_ip, geo_redirect_cc, test_suite_id):
    """
    Makes an API call with the given parameters, including the test suite ID.
    """
    # Define the API endpoint
    http_request = requests.Session()
    http_request.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    
    path = f"/test-management/v3/functional/test-suites/{test_suite_id}/test-cases"

    headers = {
        "accept": "application/json",
        "content-type": "application/json"}

    payload = [
            {
            "clientProfile": {
                "client": "CHROME",
                "ipVersion": "IPV4"
            },
            "condition": {'conditionExpression': 'Redirect response code is one of "'+str(int(status_code))+'" and location is "'+str(destination_url)+'"'},
            "testRequest": {
                "encodeRequestBody": True,
                "requestMethod": "GET",
                "testRequestUrl": source_url
            }  
 
        }
    ]

    #print(payload[0]["testRequest"]["requestHeaders"])

    geo_redirect_ip = str(geo_redirect_ip)
    if geo_redirect_ip != "nan":
        payload[0]["testRequest"]["requestHeaders"] = [
            {
                "headerAction": "ADD",
                "headerName": "X-Forwarded-For",
                "headerValue": geo_redirect_ip
            }
        ]

    # Perform the API_CALL_2
    try:
        http_response = http_request.post(urljoin(baseurl, path),headers=headers,json=payload)  # Pass payload here        
        http_response.raise_for_status()  # Raise an error for HTTP error responses
        http_status_code= http_response.status_code
        #return http_response.json()  # Assuming the API returns JSON
        #print(f"HTTP Status Code: {http_response.status_code}")
        #print("Response Body:", http_response.text)  # Log the response body for debugging
        http_response.close()
        return http_status_code
    except requests.exceptions.RequestException as e:
        print(f"ERROR - API_CALL_2 failed for {source_url}: {e}")
        return None

# API_CALL3: List all test cases in a test suite - NOT NEEDED
def make_api_call_3(test_suite_id):
    # Define the API http request
    http_request = requests.Session()
    http_request.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    
    path = f"/test-management/v3/functional/test-suites/{test_suite_id}/test-cases"
    headers = {}
    headers["accept"]="application/json"
    http_request.headers = headers
    
    # Perform the API_CALL_3
    try:
        http_response = http_request.get(urljoin(baseurl, path))
        http_response.raise_for_status()  # Raise an error for HTTP error responses
        #http_status_code= http_response.status_code
        print(http_response.json())
        http_response.close()
        return None
    except requests.exceptions.RequestException as e:
        print(f"API_CALL_3 failed: {e}")
        return None

# API_CALL4: List all conditions - NOT NEEDED
def make_api_call_4():
    # Define the API http request
    http_request = requests.Session()
    http_request.auth = EdgeGridAuth.from_edgerc(edgerc, section)
    
    path = "/test-management/v3/functional/test-catalog/conditions"
    headers = {}
    headers["accept"]="application/json"
    http_request.headers = headers
    
    # Perform the API_CALL_4
    try:
        http_response = http_request.get(urljoin(baseurl, path))
        http_response.raise_for_status()  # Raise an error for HTTP error responses
        #http_status_code= http_response.status_code
        #print(http_response.json())
        #print("Response Body:", http_response.text)  # Log the response body for debugging

        http_response.close()
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR - API_CALL_4 failed: {e}")
        return None

# Main function
def main(file_path, test_suite_name):
    # Get the test_suite_id based on the test_suite_name
    test_suite_id=str(make_api_call_1(test_suite_name))
    #make_api_call_3(test_suite_id)
    #make_api_call_4()
    """
    Reads the Excel file, processes each row, and issues an API call.
    """
    # Load the Excel file
    try:
        data = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return

    # Iterate over each row
    for index, row in data.iterrows():
        source_url = row['source_url']
        destination_url = row['destination_url']
        status_code = row['status_code']
        geo_redirect_ip = row['geo_redirect_ip']
        geo_redirect_cc = row['geo_redirect_cc']

        # Make the API call
        if source_url == destination_url:
            print("ERROR - For "+source_url+", the source and destination urls are the same. A test case will not be created. Do not implement such redirection in cloudlet!!!???!!!")
            print()
        else:
            response = make_api_call_2(source_url,destination_url,status_code,geo_redirect_ip,geo_redirect_cc,test_suite_id)
            # Log or process the response
            if response not in range (200, 299):
                print(f"ERROR - API call failed for {source_url}: with response code {response}")

                print()
            #else:
            #    print(f"SUCCESS - API call successful for {source_url}: with response code {response}")
            #    print()

# Entry point
if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Process an Excel file and make API calls.")
    parser.add_argument('--input_file', required=True, help="Path to the input Excel file.")
    parser.add_argument('--test_suite_name', required=True, help="Test Suite Name to include in the API calls.")
    
    args = parser.parse_args()

    # Process the provided Excel file
    main(args.input_file, args.test_suite_name)
