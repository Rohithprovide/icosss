import requests
import urllib.parse
from bs4 import BeautifulSoup
import logging
import time
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleSearchEngine:
    def __init__(self, use_fallback=True):
        self.AD_KEYWORDS = [
            'ad', 'ads', 'anuncio', 'annuncio', 'annonce', 'Anzeige', '广告', '廣告',
            'Reklama', 'Реклама', 'Anunț', '광고', 'annons', 'Annonse', 'Iklan',
            '広告', 'Augl.', 'Mainos', 'Advertentie', 'إعلان', 'Գովազդ', 'विज्ञापन',
            'Reklam', 'آگهی', 'Reklāma', 'Reklaam', 'Διαφήμιση', 'מודעה', 'Hirdetés',
            'Anúncio', 'Quảng cáo', 'โฆษณา', 'sponsored', 'patrocinado', 'gesponsert',
            'Sponzorováno', '스폰서', 'Gesponsord', 'Sponsorisé'
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',  # Disable compression to avoid encoding issues
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.cookies = {
            'CONSENT': 'PENDING+987',
            'SOCS': 'CAESHAgBEhIaAB'
        }
        
        self.use_fallback = use_fallback
    
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
        
        # Multiple selectors to find search result containers in different Google layouts
        result_containers = (
            soup.find_all('div', class_='g') or
            soup.find_all('div', {'data-ved': True}) or
            soup.find_all('div', class_='tF2Cxc') or
            soup.find_all('div', class_='yuRUbf') or
            soup.find_all('div', class_='Gx5Zad')
        )
        
        # Also try to find all links with titles (fallback method)
        if not result_containers:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                h3 = link.find('h3')
                if h3 and link.get('href', '').startswith('/url?'):
                    # Create a fake container for this link
                    result_containers.append(link.parent)
        
        logger.debug(f"Found {len(result_containers)} potential result containers")
        
        for container in result_containers:
            try:
                # Multiple ways to find title
                title_elem = (
                    container.find('h3') or
                    container.find('h2') or
                    container.find('a', href=True)
                )
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text().strip()
                if not title or len(title) < 3:
                    continue
                
                # Multiple ways to find URL
                link_elem = (
                    container.find('a', href=True) or
                    title_elem if title_elem.name == 'a' else None
                )
                
                if not link_elem:
                    continue
                
                url = self.clean_url(link_elem.get('href', ''))
                if not url or url.startswith('#') or 'google.com' in url:
                    continue
                
                # Extract description/snippet with multiple strategies
                description = ""
                
                # Strategy 1: Look for common description classes
                desc_elem = (
                    container.find('span', class_='st') or
                    container.find('div', class_='s') or
                    container.find('div', class_='VwiC3b') or
                    container.find('span', class_='aCOpRe')
                )
                
                if desc_elem:
                    description = desc_elem.get_text().strip()
                else:
                    # Strategy 2: Look for text content in divs
                    desc_divs = container.find_all(['div', 'span', 'p'])
                    for div in desc_divs:
                        text = div.get_text().strip()
                        # Look for description-like content
                        if (30 < len(text) < 400 and 
                            not self.has_ad_content(text) and
                            title.lower() not in text.lower()):
                            description = text
                            break
                
                # Skip if this looks like an ad result
                if self.has_ad_content(title) or self.has_ad_content(description):
                    continue
                
                # Skip if URL doesn't look like a real website
                if not url.startswith('http'):
                    continue
                
                results.append({
                    'title': title,
                    'url': url,
                    'description': description
                })
                
                logger.debug(f"Extracted result: {title[:50]}... -> {url[:50]}...")
                
            except Exception as e:
                logger.debug(f"Error extracting result: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(results)} search results")
        return results
    
    def search(self, query, num_results=15, retry_count=3):
        """Perform Google search and return clean results."""
        
        if not query or len(query.strip()) < 1:
            return {'error': 'Query cannot be empty'}
        
        # Sanitize query
        query = query.strip()[:500]  # Limit query length
        
        # Build search URL - try different parameters
        encoded_query = urllib.parse.quote_plus(query)
        # Try without gbv=1 first, as it might be causing the JavaScript requirement
        search_url = f"https://www.google.com/search?num={num_results}&q={encoded_query}"
        
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
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Log some debug info about the response
                logger.debug(f"Response content length: {len(response.content)}")
                logger.debug(f"Response contains 'did not match': {'did not match' in response.text}")
                
                # Extract results before heavy filtering to preserve structure
                results = self.extract_search_results(soup)
                
                # If no results found, try with minimal filtering
                if not results:
                    logger.warning("No results found, trying with minimal filtering")
                    # Just remove scripts but keep structure for debugging
                    for script in soup.find_all('script'):
                        script.decompose()
                    results = self.extract_search_results(soup)
                
                # If still no results, let's debug what we're getting
                if not results:
                    logger.error("Still no results found, debugging response")
                    # Check if this is a CAPTCHA or blocked response
                    try:
                        response_text = response.text
                    except UnicodeDecodeError:
                        # Handle encoding issues
                        response_text = response.content.decode('utf-8', errors='ignore')
                    
                    if any(keyword in response_text.lower() for keyword in ['captcha', 'blocked', 'automated']):
                        return {'error': 'Search blocked by Google. Please try again later.'}
                    
                    # Check for JavaScript requirement
                    if 'noscript' in response_text.lower() and 'enablejs' in response_text:
                        logger.warning("Google requires JavaScript, trying with gbv=1")
                        # Try with gbv=1 parameter
                        alt_search_url = f"https://www.google.com/search?gbv=1&num={num_results}&q={encoded_query}"
                        if search_url != alt_search_url:
                            logger.info("Retrying with gbv=1 parameter")
                            alt_response = requests.get(
                                alt_search_url,
                                headers=self.headers,
                                cookies=self.cookies,
                                timeout=10
                            )
                            if alt_response.status_code == 200:
                                alt_soup = BeautifulSoup(alt_response.content, 'html.parser')
                                alt_results = self.extract_search_results(alt_soup)
                                if alt_results:
                                    return {
                                        'query': query,
                                        'results': alt_results,
                                        'total_results': len(alt_results),
                                        'timestamp': datetime.now().isoformat()
                                    }
                        # If Google isn't working and fallback is enabled, try DuckDuckGo
                        if self.use_fallback:
                            logger.info("Google failed, falling back to DuckDuckGo")
                            return self.search_duckduckgo(query, num_results)
                        return {'error': 'Google requires JavaScript which is not supported.'}
                    
                    # Check for "did not match" message
                    if 'did not match' in response_text:
                        return {'error': 'No matching results found for this query.'}
                    
                    # Check if response is compressed/garbled
                    if len(response_text) < 1000 or response_text.count('�') > 10:
                        logger.warning("Response appears to be compressed or corrupted")
                        return {'error': 'Received corrupted response from Google. Please try again.'}
                    
                    # Debug: save first 500 readable chars of response
                    readable_content = ''.join(c for c in response_text[:500] if ord(c) < 128)
                    logger.debug(f"Readable response preview: {readable_content}")
                    
                    return {'error': 'Could not extract results from Google response. The page structure may have changed.'}
                
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
        
        # Final fallback to DuckDuckGo if Google completely fails
        if self.use_fallback:
            logger.info("Google search failed completely, trying DuckDuckGo as fallback")
            return self.search_duckduckgo(query, num_results)
        
        return {'error': 'Search failed after multiple attempts'}
    
    def search_duckduckgo(self, query, num_results=15):
        """Fallback search using DuckDuckGo HTML search."""
        try:
            logger.info(f"Searching DuckDuckGo for: {query}")
            
            # DuckDuckGo search URL
            encoded_query = urllib.parse.quote_plus(query)
            ddg_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            ddg_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(ddg_url, headers=ddg_headers, timeout=10)
            
            if response.status_code != 200:
                return {'error': 'DuckDuckGo search failed'}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Extract DuckDuckGo results
            result_links = soup.find_all('a', class_='result__a')
            
            for i, link in enumerate(result_links[:num_results]):
                try:
                    title = link.get_text().strip()
                    url = link.get('href', '')
                    
                    if not title or not url:
                        continue
                    
                    # Clean the URL (DuckDuckGo sometimes uses redirects)
                    url = self.clean_url(url)
                    
                    # Get description from the result snippet
                    description = ""
                    result_container = link.find_parent('div', class_='result')
                    if result_container:
                        snippet = result_container.find('a', class_='result__snippet')
                        if snippet:
                            description = snippet.get_text().strip()
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'description': description
                    })
                    
                except Exception as e:
                    logger.debug(f"Error extracting DuckDuckGo result: {e}")
                    continue
            
            if results:
                return {
                    'query': query,
                    'results': results,
                    'total_results': len(results),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'DuckDuckGo'
                }
            else:
                return {'error': 'No results found on DuckDuckGo'}
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return {'error': 'DuckDuckGo search failed'}