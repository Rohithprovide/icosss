import requests
import urllib.parse
from bs4 import BeautifulSoup
import logging
import time
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleSearchEngine:
    def __init__(self):
        self.AD_KEYWORDS = [
            'ad', 'ads', 'anuncio', 'annuncio', 'annonce', 'Anzeige', '广告', '廣告',
            'Reklama', 'Реклама', 'Anunț', '광고', 'annons', 'Annonse', 'Iklan',
            '広告', 'Augl.', 'Mainos', 'Advertentie', 'إعلان', 'Գովազդ', 'विज्ञापन',
            'Reklam', 'آگهی', 'Reklāma', 'Reklaam', 'Διαφήμιση', 'מודעה', 'Hirdetés',
            'Anúncio', 'Quảng cáo', 'โฆษณา', 'sponsored', 'patrocinado', 'gesponsert',
            'Sponzorováno', '스폰서', 'Gesponsord', 'Sponsorisé'
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0',
            'Accept-Language': 'en;q=1.0'
        }
        
        self.cookies = {
            'CONSENT': 'PENDING+987',
            'SOCS': 'CAESHAgBEhIaAB'
        }
    
    def has_ad_content(self, text):
        """Check if text contains ad-related content."""
        if not text:
            return False
        clean_text = ''.join(filter(str.isalpha, text))
        return (clean_text.upper() in [k.upper() for k in self.AD_KEYWORDS] or 'ⓘ' in text)
    
    def clean_url(self, url):
        """Remove Google redirect tracking from URLs."""
        if not url:
            return url
            
        # Handle Google redirect URLs
        if url.startswith('/url?'):
            try:
                # Extract the actual URL from Google's redirect
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                if 'q' in parsed:
                    url = parsed['q'][0]
            except:
                pass
        
        # Remove tracking parameters
        tracking_params = ['utm_', 'ref_src', 'gclid', 'fbclid', '_ga', '_gl']
        try:
            parsed_url = urllib.parse.urlparse(url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Filter out tracking parameters
            clean_params = {k: v for k, v in query_params.items() 
                          if not any(k.startswith(track) for track in tracking_params)}
            
            clean_query = urllib.parse.urlencode(clean_params, doseq=True)
            clean_url = urllib.parse.urlunparse((
                parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                parsed_url.params, clean_query, parsed_url.fragment
            ))
            return clean_url
        except:
            return url
    
    def filter_html_content(self, soup):
        """Remove ads, tracking, and unwanted content from HTML."""
        
        # Remove all JavaScript
        for script in soup.find_all('script'):
            script.decompose()
        
        # Remove Google logos and branding images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'googlelogo' in src or 'google.com/images/branding' in src:
                img.decompose()
        
        # Remove ad containers
        for div in soup.find_all('div', recursive=True):
            ad_spans = [span for span in div.find_all('span', recursive=True) 
                       if self.has_ad_content(span.get_text())]
            if ad_spans:
                div.decompose()
        
        # Remove privacy/terms footer elements
        for div in soup.find_all('div'):
            text = div.get_text().lower()
            if len(text) < 200 and any(term in text for term in ['privacy', 'terms', 'mumbai', 'maharashtra']):
                div.decompose()
        
        # Remove image sections with 'Images' and 'View all'
        for div in soup.find_all('div', class_='ezO2md'):
            text = div.get_text()
            if 'Images' in text and 'View all' in text:
                div.decompose()
        
        # Remove privacy/terms links
        for link in soup.find_all('a'):
            text = link.get_text().lower()
            if 'privacy' in text or 'terms' in text:
                parent = link.parent
                if parent and len(parent.get_text()) < 100:
                    parent.decompose()
        
        return soup
    
    def extract_search_results(self, soup):
        """Extract clean search results from filtered HTML."""
        results = []
        
        # Find search result containers
        result_containers = soup.find_all('div', class_='g') or soup.find_all('div', {'data-ved': True})
        
        for container in result_containers:
            try:
                # Extract title
                title_elem = container.find('h3')
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                if not title:
                    continue
                
                # Extract URL
                link_elem = container.find('a', href=True)
                if not link_elem:
                    continue
                
                url = self.clean_url(link_elem['href'])
                if not url or url.startswith('#'):
                    continue
                
                # Extract description/snippet
                description = ""
                desc_divs = container.find_all('div')
                for div in desc_divs:
                    text = div.get_text().strip()
                    # Look for description-like content
                    if len(text) > 50 and len(text) < 500 and not self.has_ad_content(text):
                        # Avoid duplicating the title
                        if title.lower() not in text.lower():
                            description = text
                            break
                
                # Skip if this looks like an ad result
                if self.has_ad_content(title) or self.has_ad_content(description):
                    continue
                
                results.append({
                    'title': title,
                    'url': url,
                    'description': description
                })
                
            except Exception as e:
                logger.debug(f"Error extracting result: {e}")
                continue
        
        return results
    
    def search(self, query, num_results=15, retry_count=3):
        """Perform Google search and return clean results."""
        
        if not query or len(query.strip()) < 1:
            return {'error': 'Query cannot be empty'}
        
        # Sanitize query
        query = query.strip()[:500]  # Limit query length
        
        # Build search URL
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?gbv=1&num={num_results}&q={encoded_query}"
        
        for attempt in range(retry_count):
            try:
                logger.info(f"Searching Google for: {query} (attempt {attempt + 1})")
                
                response = requests.get(
                    search_url,
                    headers=self.headers,
                    cookies=self.cookies,
                    timeout=10
                )
                
                # Check for CAPTCHA
                if 'captcha-form' in response.text:
                    logger.warning("CAPTCHA detected")
                    return {'error': 'Search temporarily blocked. Please try again later.'}
                
                # Check response status
                if response.status_code != 200:
                    logger.warning(f"HTTP {response.status_code} response")
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return {'error': 'Search service unavailable'}
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Filter content
                soup = self.filter_html_content(soup)
                
                # Extract results
                results = self.extract_search_results(soup)
                
                if not results:
                    return {'error': 'No results found'}
                
                return {
                    'query': query,
                    'results': results,
                    'total_results': len(results),
                    'timestamp': datetime.now().isoformat()
                }
                
            except requests.exceptions.Timeout:
                logger.warning(f"Search timeout (attempt {attempt + 1})")
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                return {'error': 'Search request timed out'}
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Search request failed: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {'error': 'Network error occurred'}
                
            except Exception as e:
                logger.error(f"Unexpected search error: {e}")
                return {'error': 'Search processing failed'}
        
        return {'error': 'Search failed after multiple attempts'}