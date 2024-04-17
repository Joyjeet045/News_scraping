
from lxml import html
import sys
import re

from lxmlparser1 import HTMLParser



from dateutil.parser import parse as date_checker
from stopwords import stop_word_lis
from stopwords import read_text_file





class CustomExtractor:
    def __init__(self,html_content):
        self.stopwords = stop_word_lis()
        self.parser = HTMLParser(html_content)
        self.class_lis = read_text_file()

    def calculate_gravity_score(self, tag):
        # Your custom logic to calculate the gravity score
        # This example uses the length of text content as a score
        # text_content = tag.get_text(strip=True)
        text_content = tag.text_content().strip()
        return len(text_content)

    def previousSiblings(self,node):
      try:
        # return [n for n in node.itersiblings(preceding=True)]
        return [n for n in self.parser.iteratesib(node=node,preceding=True)]
      except:
        return []
    def nieghbourhood_aggregation(self, node):
        # Iterate over siblings
        return self.previousSiblings(node)

    def linkage(self, node):

        # For simplicity, this example checks if the node contains more than 5 links
        # links = node.find_all('a')
        links = self.parser.find_all_lxml(node=node,tag='a')
        return len(links) > 5


    def boost_req(self, node):
        para = "p"
        steps_away = 0
        minimum_stopword_count = 2
        max_stepsaway_from_node = 3

        text_containers = self.nieghbourhood_aggregation(node)
        # print(len(text_containers))
        for current_node in text_containers:
            # current_node_tag = current_node.name
            current_node_tag = current_node.tag
            if current_node_tag == para:
                if steps_away >= max_stepsaway_from_node:
                    return False
                # paragraph_text = current_node.get_text(strip=True)
                paragraph_text = current_node.text_content().strip()
                word_stats = self.stop_words_chck(paragraph_text)
                # print(word_stats)
                if word_stats > minimum_stopword_count:
                    return True
                steps_away += 1
        return False

    def stop_words_chck(self, text):
        text = re.sub(r'[^\w\s]', '', text)
        words = [word.lower() for word in text.split()]

        sm = 0
        for word in words:
          if(word in self.stopwords):
            sm+=1
        return sm


    def count_paragraph_tags_on_same_level_with_depth(self,element, depth=0):
        # paragraph_tags = element.find_all('p', recursive=False)
        paragraph_tags = self.parser.find_all_lxml(node=element,tag='p', recursive=False)
        if paragraph_tags:
            return len(paragraph_tags), depth
        # for child in element.children:
        for child in element.getchildren():
            try:
                num_paragraphs, child_depth = self.count_paragraph_tags_on_same_level_with_depth(child, depth=depth+1)
            except:
                continue
            if num_paragraphs:
                return num_paragraphs, child_depth
        return 0, 0


    def count_br_tags_on_same_level_with_depth(self,element, depth=0):
        # paragraph_tags = element.find_all('br', recursive=False)
        paragraph_tags = self.parser.find_all_lxml(node=element,tag='br', recursive=False)
        if paragraph_tags:
            return len(paragraph_tags), depth
        # for child in element.children:
        for child in element.getchildren():
            try:
                num_paragraphs, child_depth = self.count_br_tags_on_same_level_with_depth(child, depth=depth+1)
            except:
                continue
            if num_paragraphs:
                return num_paragraphs, child_depth
        return 0, 0



    def most_imp_node(self, parser):
        top_node = None
        top_node_score = 0
        worthy_text_containers = self.worthy_text_containers(parser)
        for clss in self.class_lis:
            
            for node in worthy_text_containers:
                
                try:
                    if(node.get('class').strip() == clss):
                        # print(node.get('class'))
                        return node
                except:
                    continue

        # print(worthy_text_containers)
        starting_boost = 1.0
        parent_text_containers = []
        text_containers_with_text = []



        for node in worthy_text_containers:
            # text_node = node.get_text()
            try:
                node.text_content().strip()
            except:
                continue
            text_node = node.text_content()
            word_stats = self.stop_words_chck(text_node)
            try:
                if(node['class'] == "atricle_content"):
                    text_containers_with_text.append(node)
            except:
                pass
            # print(len(node.get_text(strip=True)))
            # print(word_stats)
            high_link_density = self.linkage(node)
            # print(high_link_density)
            if word_stats >= 2 and not high_link_density:
                # print("Yes")
                text_containers_with_text.append(node)

        

        # print(text_containers_with_text)
        for node in text_containers_with_text:

            boost_score = 0
            depth = 0

            boost_score3 = 0
            depth3 = 0

            try:
                boost_score, depth = self.count_paragraph_tags_on_same_level_with_depth(node)
    #                print(node['class'], " ", boost_score)
            except:
                boost_score = 0

            try:
              boost_score3, depth3 = self.count_br_tags_on_same_level_with_depth(node)
            except:
              depth3 += 0

            text_node = node.text_content().strip()
            word_stats = self.stop_words_chck(text_node)/2
            temp = 0

            try:
                temp = len(node.content)
            except:
                pass

            boost_score2 = 0
            if(self.boost_req(node)):

              boost_score2 = 5

            try:
              if 'article' in node.get('class').split():
                word_stats += 10
            except:
                word_stats += 0
            try:
              if 'content' in node.get('class').split():
                word_stats += 10
            except:
                word_stats += 0

            
            boost_score = boost_score*(0.95**(depth+1))
            upscore = word_stats + boost_score + boost_score2 + boost_score3*(0.95**(depth3+1))


            parent_node = node.getparent()

            self.update_score(node,upscore)

            zt = self.get_score(node)
            if(zt > top_node_score):
            
              top_node = node
              top_node_score = zt


            # print(node.name," ",word_stats," ",boost_score," ",boost_score3," ",node['score']," ",upscore)

            parent_text_containers.append(node)

            x = node
            if(node.tag == 'p'):
                for i in range(5):
                    # x = x.parent
                    x = x.getparent()
                    self.update_score(x,upscore*((0.8)**i))

            if parent_node not in parent_text_containers:
                parent_text_containers.append(parent_node)

            # parent_parent_node = parent_node.parent
            parent_parent_node = parent_node.getparent()
            if parent_parent_node is not None:
                self.update_node_count(parent_parent_node, 1)

                if parent_parent_node not in parent_text_containers:
                    parent_text_containers.append(parent_parent_node)


        # print(len(parent_text_containers))
        for e in parent_text_containers:
            # print(node.name," ",node['score'])
            score = self.get_score(e)

            if score > top_node_score:
#                 print(node.name," ",node['score'])
                top_node = e
                top_node_score = score

            if top_node is None:
                top_node = e

        return top_node

    def worthy_text_containers(self, parser):
        worthy_text_containers = []
        for tag in ['div','p', 'pre', 'td','header','article','main']:
            # items = parser.find_all(tag)
            items = self.parser.find_all_lxml(tag=tag)
            for i in items:
                for j in i:
                    
                    worthy_text_containers.append(j)           
            # worthy_text_containers += items
        # print(type(worthy_text_containers)," ",len(worthy_text_containers[0])," ",)
        return worthy_text_containers


    def update_score(self, node, score):
        if 'score' not in node:
            # node['score'] = len(node.get_text(strip=True))**(0.5)
            # node['score'] = len(node.text_content().strip())**(0.5)
            node.set('score', str(len(node.text_content().strip())**(0.5)))

        # node['score'] += score
        current_score_str = node.get('score', '0')
        current_score = float(current_score_str)  

        new_score = current_score + score 

        node.set('score', str(new_score)) 

    def update_node_count(self, node, count):
        if 'count' not in node:
            # node['count'] = 0
            node.set('count', '0')

        # node['count'] += count
        current_score_str = node.get('count', '0')
        current_score = float(current_score_str)  

        new_score = current_score + count 

        node.set('count', str(new_score)) 

    def get_score(self, node):
        return float(node.get('score', '0'))



    def findauthors(self, doc):
         #we are using mutiple rules simultanously so it can copy a name mutiple times
        def unique_list(authors):
            return list(set([item.title() for item in authors if len(item.split()) <= 5]))

        
        
        # as names do not contain digits
        def contains_digits(d):
            for char in d:
                if char.isdigit():
                    return True
            return False
        # to filter output written by tag text or content
        def filter(str):
            
            str = ''.join(char for char in str if char != '<' and char != '>')

            str = re.sub(r'\b(by:|by|from:|image|of|real|oru|development|apr|three|minors|killed|fire|pokhara|tourism|council|hands|memo|biotechnology|nbspjanuary|lifestyle|travel|times|public|company|source|screen|korea|battery|glass|screengrab|edited|close|com|october|to|bookmark|writer|laboratory|fast|staff|editor|the|concerned|india|familiar|with|integrated|view|comments|am|pm|updated|published|hd|doc|for|staying|indonesia|english|live|share|whatsapp|telegram|facebook|twitter|email|linkedin|advertisement|news|in|media|bureau)\b', '', str, flags=re.IGNORECASE).strip()

            str = str.replace('"', ' ').replace("'", ' ').replace('-', ' ').replace('.', ' ')

            names = re.findall(r'\w+|\,',str)

    
            authors = []
            current_author = ''

            for name in names:
                if contains_digits(name):
                    continue
                elif name in ['and', ',']:
                    if current_author:
                        authors.append(current_author.strip())
                        current_author = ''
                else:
                    current_author += name + ' '
            #sometimes last element may be news source 
            if len(current_author)>2:
                authors.append(current_author.strip())
    
            return authors
            
       
        attribute_name = ['name', 'rel', 'itemprop', 'class', 'id','route']
        attribute_value = ['uk-link-reset','info_l','Page-authors','news-detail_newsBy__6_pzA','xf8Pm byline','writer','art_sign','reviewer','read__credit__item','tjp-meta__label','article-author','article-byline__author','cursor-pointer','credit__authors','author', 'byline', 'dc.creator', 'byl','author-name','author-content','aaticleauthor_name','group-info','byline_names','article__author','article-byline__author','Byline','h6 h6--author-name'
                          ]
        
        pattern= re.compile(r'(?:written by|writer|editor|with reports from|source|edited by|published by)[\s:-]+([A-Za-z]+(?:\s+[A-Za-z]+)?)', re.IGNORECASE)
        
        parser=HTMLParser(doc)
        

           
        data_objects = []
        authors = []
        
        for attribute in attribute_name:
            for value in attribute_value:
                found = parser.attributeobjects(attribute, value)
                data_objects.extend(found)
    
        for element in data_objects:
            name = ''
            if element.tag == 'meta':
                name = element.get('content', '') 
            else:
                name = element.text_content().strip()
                
                
            if len(name) > 0:
                authors.extend(filter(name))
        #it search for pattern described in whole text
        match = pattern.search(parser.all_text())

        if match:
            authors.extend(filter(match.group(1)))
    
        return unique_list(authors)

    
    def findauthors(self, doc):
         #we are using mutiple rules simultanously so it can copy a name mutiple times
        def unique_list(authors):
            return list(set([item.title() for item in authors if len(item.split()) <= 5]))

        
        
        # as names do not contain digits
        def contains_digits(d):
            for char in d:
                if char.isdigit():
                    return True
            return False
        # to filter output written by tag text or content
        def filter(str):
            #filtering < or > if by any chance through comments etc.
            str = ''.join(char for char in str if char != '<' and char != '>')
            #removing all unecessary words which can't be part of name
            str = re.sub(r'\b(by:|by|from:|image|of|real|oru|development|three|minors|killed|fire|pokhara|tourism|council|hands|memo|biotechnology|nbspjanuary|lifestyle|travel|times|public|company|source|screen|korea|battery|glass|screengrab|edited|close|com|mar|on|first|october|to|bookmark|writer|laboratory|fast|staff|editor|the|concerned|india|familiar|with|integrated|view|comments|am|pm|updated|published|hd|doc|for|staying|indonesia|english|live|share|whatsapp|telegram|facebook|twitter|email|linkedin|advertisement|news|in|media|bureau)\b', '', str, flags=re.IGNORECASE).strip()
            #removing all inverted commas and full stop
            str = str.replace('"', ' ').replace("'", ' ').replace('-', ' ').replace('.', ' ')
            #breaking string in list of words considering comma as also word
            names = re.findall(r'\w+|\,',str)

            #joining words to name using 'and' and comma as name end
            authors = []
            current_author = ''

            for name in names:
                if contains_digits(name):
                    continue
                elif name in ['and', ',']:
                    if current_author:
                        authors.append(current_author.strip())
                        current_author = ''
                else:
                    current_author += name + ' '
            #sometimes last element may be news source 
            if len(current_author)>2:
                authors.append(current_author.strip())
    
            return authors
            
       
        attribute_name = ['name', 'rel', 'itemprop', 'class', 'id','route']
        attribute_value = ['uk-link-reset','info_l','Page-authors','float-left update','news-detail_newsBy__6_pzA','xf8Pm byline','writer','art_sign','reviewer','read__credit__item','tjp-meta__label','article-author','article-byline__author','cursor-pointer','credit__authors','author', 'byline', 'dc.creator', 'byl','author-name','author-content','aaticleauthor_name','group-info','byline_names','article__author','article-byline__author','Byline','h6 h6--author-name'
                          ]
        #for searching  pattern for author
        pattern= re.compile(r'(?:written by|writer|editor|with reports from|source|edited by|published by)[\s:-]+([A-Za-z]+(?:\s+[A-Za-z]+)?)', re.IGNORECASE)
        #defining parser object
        parser=HTMLParser(doc)
        
        #to store all object return by function
        data_objects = []
        # to store authors name string
        authors = []
        # finding all data objects
        for attribute in attribute_name:
            for value in attribute_value:
                found = parser.attributeobjects(attribute, value)
                data_objects.extend(found)
        #extracting content of data objects
        for element in data_objects:
            name = ''
            if element.tag == 'meta':
                name = element.get('content', '') 
            else:
                name = element.text_content().strip()
                
                
            if len(name) > 0:
                authors.extend(filter(name))
        #it search for pattern described in whole text
        match = pattern.search(parser.all_text())
        # appending the firts match by group 1
        if match:
            authors.extend(filter(match.group(1)))
    
        return unique_list(authors)

    def finddate(self,doc,url):
        #function to check for date is valid or not
        def check_date(date_str):
            if date_str:
                try:
                    #if we not remove comma, it might return none as invalid date
                    cleaned_date_str = date_str.replace(',', '')
                    
                    return date_checker(cleaned_date_str)
                except (ValueError, OverflowError, AttributeError, TypeError):
                    return None
            else:
                return None
        #all patrerns of date
        STRICT_DATE_REGEX = re.compile(r'\/(\d{4})\/(\d{2})\/(\d{2})\/')
        date_patterns = [re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})', re.IGNORECASE),
                        re.compile(r'\d{4}-\d{2}-\d{2} [A-Za-z]{2}[A-Za-z]*T', re.IGNORECASE),
                        re.compile(r'([a-zA-Z]+?\s?\d{1,2}\s?\,?\s?\d{4}\s?,?\s?\d{1,2}:\d{2}(?:\s?[APMapm]{2}\s?| IST\s?))|(\d{2}\s*[a-zA-Z]+\s*\d{4})\s*,?\s*(\d{1,2}:\d{2}(?:\s?[APMapm]{2}\s?| IST\s?))', re.IGNORECASE),
                        re.compile(r'([a-zA-Z]+?\s?\d{1,2}\s?\,?\s?\d{4}(?:\s?|\s*,\s*)|(\d{2}\s*[a-zA-Z]+\s*\d{4}))', re.IGNORECASE),
                        re.compile(r'(\w+\s+\d{1,2},?\s+\d{4})\s*\|\s*(\d{1,2}:\d{2}\s*[APMapm]{2}\s*PT)', re.IGNORECASE)]
        #it is for matching in group(0) that means only 1 pattern atmost is present in which it is passed
        def patternmatch(str):
            date_regix=STRICT_DATE_REGEX
            date_match = date_regix.search(str)
            if date_match:
                date_str = date_match.group(0)
                if(date_str):
                    return date_str
            #another date pattern search
            date_regix = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
            date_match = date_regix.search(str)
            if date_match:
                date_str = date_match.group(0)
                if(date_str):
                    return date_str
                    


            for pattern in date_patterns:
                alt_date_match = pattern.search(str)
                if alt_date_match:
                    date_str = alt_date_match.group(0)
                    if(date_str):
                        return date_str

            return None
        
        #defining parser object
        parser=HTMLParser(doc)
        html_text=parser.all_text()

        
        
        attribute_name= ['id', 'class','name','rel', 'itemprop', 'pubdate', 'property']
        attribute_value=['art_plat','info_l','bar','value-title','post-time','news-detail_newsInfo__dv0be','post-tags','bread-crumb-detail__time','fa fa-clock-o','post-timeago','entry-date published','detail__time','article-publish article-publish--','title_text','title-text','thb-post-date','entry-sidebar','meta_date','txt','news-detail','post-timeago','read__time','box','where','txt_left','date-publish','published','article-publish','timestamp','article_date_original', 'article:published_time','inputDate','bread-crumb-detail__time', 'inputdate','date', 'OriginalPublicationDate', 'publication_date', 'publish_date', 'PublishDate', 'rnews:datePublished', 'sailthru.date', 'datePublished', 'dateModified', 'og:published_time'
                        ]

        #attribute pattern search for word in attribute values not exact attribute value and data objects for storing objects
        data_objects=[]
        for attribute in attribute_name:
            for value in attribute_value:
                matches =parser.attributepattern(attribute,value)
                data_objects.extend(matches)
        #extracting data of data objects checking them as valid date or not
        for element in data_objects:
            str_content=element.text_content().strip()
            datetime = check_date(str_content)
            if datetime:
                return datetime
            else:
                str=patternmatch(str_content)
                
                if str:
                    date = check_date(str)
                    
                    if date:
                        return date
             
            if element.tag == 'meta':
                str_content = element.get('content', '') 
                datetime = check_date(str_content)
                if datetime:
                    return datetime
        #some south east asian websites uses dates in url
        date = patternmatch(url)
        if date:
            datetime = check_date(date)
            if datetime:
                return datetime

        
        # to serach strict date rigix if any in whole html text
        
        date_match = STRICT_DATE_REGEX.search(html_text)
        if date_match:
            date_str = date_match.group(1)
            datetime = check_date(date_str)
            if datetime:
                return datetime
        
        #changing pattern to dated standard pattern having - in between
        STRICT_DATE_REGEX = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
        date_match = STRICT_DATE_REGEX.search(html_text)
        if date_match:
            date_str = date_match.group(1)
            datetime = check_date(date_str)
            if datetime:
                return datetime
        
         # to search for date if it have random date class neither strict date regix
        for pattern in date_patterns:
            alt_date_match = pattern.search(html_text)
            if alt_date_match:
                date_str = alt_date_match.group(1)
                if check_date(date_str) is not None:
                    datetime = check_date(date_str)
                    if datetime:
                        return datetime
       
        return None
    
    



    def extract_best_part(self,title, splitter, ans=None):
        """Extracts the most relevant part of the title"""
        best_length = 0
        best_index = 0
        title_pieces = title.split(splitter)
        if ans and ans != '':
            ans_filter = re.compile(r'[^a-zA-Z0-9\ ]')
            ans = ans_filter.sub('', ans).lower()

        for i, title_piece in enumerate(title_pieces):
            current = title_piece.strip()
            if ans and ans in ans_filter.sub('', current).lower():
                best_index = i
                break
            if len(current) > best_length:
                best_length = len(current)
                best_index = i
        title = title_pieces[best_index]
        return title    

    def fetch_title(self,parser):
        
        extracted_title = ''
        title_elements = parser.find_all_tags('title')

        if title_elements is None or len(title_elements) == 0:
            print("Error")
            return extracted_title

        # Title element found
        title_text = parser.get_text_by_tag(title_elements[0]['tag'])[0]
        used = False

        title_text_h1 = ''
        title_element_h1_list = parser.find_all_tags('h1')
        
        title_text_h1_list = [parser.get_text_by_tag(tag_name=tag['tag'],attribute_name='class',attribute_value=tag['attributes'].get('class', None))[0] for tag in title_element_h1_list]

        if title_text_h1_list:
            title_text_h1_list.sort(key=len, reverse=True)
            title_text_h1 = ' '.join([x for x in title_text_h1_list[0].split() if x])

        meta_tag_content = parser.find_all_by_attribute(attribute_name='property', attribute_value='og:title')
        if not meta_tag_content:
            meta_tag_content = parser.find_all_by_attribute(attribute_name='name', attribute_value='og:title')
        title_text_meta = parser.get_text_by_tag(meta_tag_content[0]['tag'])[0] if meta_tag_content else ''
        filter_regex = re.compile(r'[^a-zA-Z0-9\ ]')
        filtered_title_text = filter_regex.sub('', title_text).lower()
        filtered_title_text_h1 = filter_regex.sub('', title_text_h1).lower()
        filtered_title_text_meta = filter_regex.sub('', title_text_meta).lower()
        
        if filtered_title_text_h1  == filtered_title_text:
            extracted_title = filtered_title_text
            used = True
        elif filtered_title_text_h1 and filtered_title_text_h1 == filtered_title_text_meta:
            extracted_title = title_text_h1
            used= True
        elif filtered_title_text_h1 and filtered_title_text_h1 in filtered_title_text and filtered_title_text_meta !='' and filtered_title_text_meta in filtered_title_text and len(title_text_h1) > len(title_text_meta):
            used = True
        elif filtered_title_text_meta and filtered_title_text_meta != filtered_title_text and filtered_title_text.startswith(filtered_title_text_meta):
            extracted_title = title_text_meta
            used = True
        separators = ['|', '–', '-', '_', '/', ' » ', ':', ';', ',', '—', '...']
        for sep in separators:
            if not used and sep in title_text:
                extracted_title = self.extract_best_part(title_text, sep, title_text_h1)
                used = True
                break
        return extracted_title

