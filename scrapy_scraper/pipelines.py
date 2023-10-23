# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
import logging
import supabase
from supabase import create_client
from scrapy.exceptions import DropItem
import re
import requests
import re
from collections import defaultdict


class AddTags_Pipeline:
    def __init__(self):
        try:
            supabase_url = "https://twbzeixlcffvikcambdk.supabase.co/"
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR3YnplaXhsY2ZmdmlrY2FtYmRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ5NTg3MTksImV4cCI6MjAxMDUzNDcxOX0.eCKXY_n8-rtrtjI4HgkGSQW-HeazctEU-qjfsVl6tdE"

            self.supabase_client = create_client(supabase_url, supabase_key)
        except Exception as e:
            print(f"Error creating Supabase client: {str(e)}")

    def process_item(self, item, spider):
        ##get industry id##
        self.table_name = "INDUSTRY"
        response = self.supabase_client.table(self.table_name).select("industry_id", "scraping_tags").execute()
        data = response.data

        #get tags in lowercase
        tag_dict = {}
        for row in data:
            lowered_tags = [tag.lower() for tag in row['scraping_tags']]
            tag_dict[row["industry_id"]] = lowered_tags

        #get all words from scraped content in lowercase
        text_words = re.findall(r'\b\w+\b', item["scraped_content"].lower())

        # Dictionary to store match counts
        industry_counts = defaultdict(int)  

        for key, values in tag_dict.items():
            count = 0  # Initialize match count for this tag
            for i in range(len(text_words)):
                pattern = r'\b\w{2,3}\b'
                matches = re.findall(pattern, text_words[i])
                if any(match in values for match in matches):
                    count += 1
            industry_counts[key] = count  # Store the match count for this tag

        # Find the industry_id with the most matches
        best_match = max(industry_counts, key=industry_counts.get)
        item["industry_id"] = best_match


        ##get sector id##
        self.table_name = "SECTOR"
        response = self.supabase_client.table(self.table_name).select("sector_id", "scraping_tags").execute()
        data = response.data

        tag_dict = {}
        for row in data:
            lowered_tags = [tag.lower() for tag in row['scraping_tags']]
            tag_dict[row["sector_id"]] = lowered_tags

        sector_counts = defaultdict(int)  # Dictionary to store match counts

        for key, values in tag_dict.items():
            count = 0  # Initialize match count for this tag
            for i in range(len(text_words)):
                pattern = r'\b\w{2,3}\b'
                matches = re.findall(pattern, text_words[i])
                # Check if any of the matched words are in the values
                if any(match in values for match in matches):
                    count += 1
            sector_counts[key] = count  # Store the match count for this tag

        # Find the sector_id with the most matches
        best_match = max(sector_counts, key=sector_counts.get)
        item["sector_id"] = best_match

        return item



class ChatGPT_Pipeline:
    def process_item(self, item, spider):
        api_key = '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'  
        api_url = 'https://api.openai.com/v1/chat/completions'

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        ##ChatGPT to summarise text##
        conversation = [
        {"role": "system", "content": "ChatGPT is acting as a summariser of legislative news for the finance industry, in newsletters catered for lawyers."},
        {"role": "user", "content": f"Please summarize the article (300 words) reporting the key information from the article in a neutral tone, using headers for each section or bullet points where there are multiple points in a sentence: '{item['scraped_content']}'"}  #to edit
        ]

        data = {
            'model': 'gpt-3.5-turbo',
            'messages': conversation,
        }

        try:
            output = requests.post(api_url, headers=headers, data=json.dumps(data))
            output = output.json()
            item['summarised_content'] = output['choices'][0]['message']['content']
        except Exception as e:
            raise DropItem(f"Error passing content into chatGPT API: {str(e)}, output: {output}")


        ##ChatGPT to summarise headline##
        conversation = [
        {"role": "system", "content": "ChatGPT is acting as a reporter of legislative news for the finance industry."},
        {"role": "user", "content": f"Please paraphrase the following headline. Do not put inverted commas: '{item['scraped_headline']}'"}  #to edit
        ]

        data = {
            'model': 'gpt-3.5-turbo',
            'messages': conversation,
        }

        try:
            output = requests.post(api_url, headers=headers, data=json.dumps(data))
            output = output.json()
            item['summarised_headline'] = output['choices'][0]['message']['content']
        except Exception as e:
            raise DropItem(f"Error passing headline into chatGPT API: {str(e)}, output: {output}")

        return item



class Supabase_Pipeline(object):

    def __init__(self):
        try:
            supabase_url = "https://twbzeixlcffvikcambdk.supabase.co/"
            supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR3YnplaXhsY2ZmdmlrY2FtYmRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE2OTQ5NTg3MTksImV4cCI6MjAxMDUzNDcxOX0.eCKXY_n8-rtrtjI4HgkGSQW-HeazctEU-qjfsVl6tdE"

            self.supabase_client = create_client(supabase_url, supabase_key)
            self.table_name = "SCRAPED_DATA"
        except Exception as e:
            print(f"Error creating Supabase client: {str(e)}")

    def process_item (self, item, spider):
        self.store_db(item)
        return item

    #push to database
    def store_db(self, item):
        try:
            data_to_ingest = {
                "author" : item['url'],
                "domain" : item['domain'],
                "datetime_scraped": item['datetime_scraped'],
                "published_date" : item['published_date'],
                "scraped_headline" : item['scraped_headline'],
                "scraped_content" : item['scraped_content'],
                "summarised_content" :item['summarised_content'],
                "summarised_headline": item['summarised_headline'],
                "related_links" : item['related_links']
            }

            response, error = self.supabase_client.table(self.table_name).upsert([data_to_ingest]).execute()

            if error:
                print("Error inserting data:", error)
            else:
                print("Data inserted successfully:", response)

        except BaseException as e:
            print(f"Error inserting data: {str(e)}, for item {item['url']}")





