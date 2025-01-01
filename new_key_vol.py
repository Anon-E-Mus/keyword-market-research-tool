from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
import time
import csv
from typing import List, Dict, Tuple
import logging
import os
import sys

class KeywordResearchTool:
    def __init__(self, client_config_path: str, customer_id: str):
        """
        Initialize the Keyword Research Tool
        
        Args:
            client_config_path (str): Path to the Google Ads API configuration file
            customer_id (str): Google Ads customer ID without dashes
        """
        if not os.path.exists(client_config_path):
            raise FileNotFoundError(f"Google Ads configuration file not found at: {client_config_path}")
            
        self.client = GoogleAdsClient.load_from_storage(client_config_path)
        self.customer_id = customer_id.replace("-", "")  # Remove any dashes from customer ID
        self.keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
        self.last_request_time = 0  # Track time of last request
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('keyword_research.log', encoding='utf-8', errors='ignore'),
                logging.StreamHandler()
            ]
        )
        #sys.stdout.reconfigure(encoding='utf-8')
        self.logger = logging.getLogger(__name__)

    def _wait_for_rate_limit(self):
        """
        Ensure we wait appropriate time between requests to respect rate limit
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < 1.5:
            sleep_time = 1.5 - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    def create_request(
        self,
        keywords: List[str],
        language_id: str,
        location_id: str,
        page_size: int = 1
    ) -> Dict:
        """
        Create a keyword ideas request
        """
        try:
            # Generate keyword ideas based on the provided keywords
            keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            
            request = {
                "customer_id": self.customer_id,
                "language": f"languageConstants/{language_id}",
                "geo_target_constants": [f"geoTargetConstants/{location_id}"],
                "keyword_plan_network": keyword_plan_network,
                "keyword_seed": {"keywords": keywords},
                "page_size": page_size
            }
            
            return request
            
        except Exception as e:
            self.logger.error(f"Error creating request: {str(e)}")
            raise

    def get_keyword_ideas(
        self,
        keywords: List[str],
        language_id: str,
        location_id: str,
        batch_size: int = 20,  # Reduced batch size for better rate limit handling
        no_ideas_to_process = 1
    ) -> Dict[str, List]:
        """
        Get keyword ideas and their metrics
        
        Args:
            keywords (List[str]): List of seed keywords
            language_id (str): Language ID for targeting
            location_id (str): Location ID for targeting
            batch_size (int): Number of keywords to process in each batch
        
        Returns:
            Dict[str, List]: Dictionary of keywords and their metrics
        """
        results = {}
        
        if not keywords:
            self.logger.warning("No keywords provided to process")
            return results
            
        # Process keywords in batches
        print("KEYWORDS no: ", len(keywords))
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1} of {(len(keywords) + batch_size - 1)//batch_size}")
            
            try:
                # Enforce rate limit
                self._wait_for_rate_limit()
                
                request = self.create_request(batch, language_id, location_id)
                response = self.keyword_plan_idea_service.generate_keyword_ideas(request=request)
                
                count = 0
                for idea in response:
                    # if count >=no_ideas_to_process:
                    #     break
                    keyword = idea.text
                    metrics = idea.keyword_idea_metrics
                    
                    results[keyword] = [
                        metrics.avg_monthly_searches,
                        self._get_competition_level(metrics.competition),
                        metrics.competition_index
                    ]
                    count += 1
                
            except GoogleAdsException as ex:
                self.logger.error(f"Request failed with status {ex.error.code().name}")
                for error in ex.failure.errors:
                    self.logger.error(f'\tError with message "{error.message}".')
                    if error.location:
                        for field_path_element in error.location.field_path_elements:
                            self.logger.error(f"\t\tOn field: {field_path_element.field_name}")
                
                # Save failed keywords to a file
                self._save_failed_keywords(batch, "failed_keywords.txt")
                
                # If we hit a rate limit error, wait longer before next request
                if ex.error.code().name == 'RESOURCE_EXHAUSTED':
                    self.logger.info("Rate limit hit, waiting 5 seconds before next request")
                    time.sleep(5)
                continue
                
            except Exception as e:
                self.logger.error(f"Unexpected error processing batch: {str(e)}")
                self._save_failed_keywords(batch, "failed_keywords.txt")
                continue
                
        return results

    def _get_competition_level(self, competition) -> str:
        """Convert competition enum to string representation"""
        competition_map = {
            0: "UNSPECIFIED",
            1: "UNKNOWN",
            2: "LOW",
            3: "MEDIUM",
            4: "HIGH"
        }
        return competition_map.get(competition, "UNKNOWN")

    def _save_failed_keywords(self, batch, filename="failed_keywords.txt"):
        with open(filename, "a", encoding="utf-8") as f:  # Specify UTF-8 encoding here
            for keyword in batch:
                f.write(f"{keyword}\n")

    def write_results_to_csv(
        self,
        results: Dict[str, List],
        output_file: str,
        language_id: str,
        location_id: str
    ):
        """Write results to CSV file"""
        with open(output_file, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Keyword",
                "Monthly Search Volume",
                "Competition Level",
                "Competition Index",
                "Language ID",
                "Location ID"
            ])
            
            for keyword, metrics in results.items():
                writer.writerow([
                    keyword,
                    metrics[0],
                    metrics[1],
                    metrics[2],
                    language_id,
                    location_id
                ])

def main():
    # Configuration
    CLIENT_CONFIG_PATH = "google-ads.yaml"
    KEYWORD_FILE = "domain.txt"
    LANGUAGE_ID = "1000"  # English
    LOCATION_ID = "2840"  # United States
    CUSTOMER_ID = ""  # Replace with your customer ID
    
    # Initialize the tool
    try:
        tool = KeywordResearchTool(CLIENT_CONFIG_PATH, CUSTOMER_ID)
        
        # Check if input file exists
        if not os.path.exists(KEYWORD_FILE):
            raise FileNotFoundError(f"Input keyword file not found: {KEYWORD_FILE}")
        
        # Read keywords from file
        with open(KEYWORD_FILE, "r", encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
        
        if not keywords:
            raise ValueError("No keywords found in input file")
        
        # Get keyword ideas
        results = tool.get_keyword_ideas(
            keywords=keywords,
            language_id=LANGUAGE_ID,
            location_id=LOCATION_ID
        )
        
        # Write results to CSV
        tool.write_results_to_csv(
            results=results,
            output_file=f"keyword_results_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            language_id=LANGUAGE_ID,
            location_id=LOCATION_ID
        )
        
    except Exception as e:
        logging.error(f"Error running keyword research tool: {str(e)}")
        raise

if __name__ == "__main__":
    main()