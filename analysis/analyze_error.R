library(tidyverse)
library(stringr)

return_outlet <- function(url) {
  if (str_detect(url, "techcrunch\\.c")) {
    return("TechCrunch")
  }
  if (str_detect(url, "washingtonpost\\.c")) {
    return("Washington Post")
  }
  if (str_detect(url, "nytimes\\.com")) {
    return("NYT")
  } 
  if (str_detect(url, "latimes\\.c")) {
    return("LA Times")
  }
  if (str_detect(url, "bloomberg\\.c")) {
    return("Bloomberg")
  }
  if (str_detect(url, "sacbee\\.c")) {
    return("Sacramento Bee")
  }
}

OLD <- '/Users/viswa/Desktop/Code/MG/gendermeme/annotated/manual/ann_dump_Fri_May_19_05_26_48_2017.tsv'
NEW <- '/Users/viswa/Desktop/Code/MG/gendermeme/annotated/manual/ann_dump_Sun_Jul_16_12_44_28_2017.tsv'
SR <- '/Users/viswa/Desktop/Code/MG/gendermeme/annotated/manual/ann_dump_sr.tsv'
error_data <- 
  read_tsv(SR)

error_data <-
  error_data %>% 
  filter(!(a_gender == "non-living" & where == "auto_only")) %>%
  filter(!(a_gender == "non-living" & str_detect(m_gender, "company"))) %>% 
  filter(!(where == "manual_only" & str_detect(m_gender, "company"))) %>% 
  filter(!(str_detect(name, "(anonymous)|(unnamed)|(unknown)"))) %>% 
  mutate(outlet = map_chr(url, return_outlet))

error_data %>% 
  group_by(outlet) %>% 
  mutate(n_articles = n_distinct(art_id)) %>% 
  count(n_articles, where) %>% 
  spread(key = where, value = n) %>% 
  ungroup() %>% 
  mutate(precision = both / (auto_only + both), recall = both / (both + manual_only)) %>% 
  arrange(desc(n_articles))

error_data %>%
  filter(where == "both") %>%
  unite(source_match, m_source, a_source) %>%
  count(source_match) %>%
  View()
  
