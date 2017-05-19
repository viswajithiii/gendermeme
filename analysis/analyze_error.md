Error Analysis: GenderMeme May 19 2017
================
Poorna Kumar
5-19-2017

-   [PRECISION AND RECALL FOR PERSON IDENTIFICATION](#precision-and-recall-for-person-identification)
-   [RECALL FOR GENDER](#recall-for-gender)
-   [PRECISION FOR GENDER](#precision-for-gender)

``` r
library(tidyverse)
```

    ## Loading tidyverse: ggplot2
    ## Loading tidyverse: tibble
    ## Loading tidyverse: tidyr
    ## Loading tidyverse: readr
    ## Loading tidyverse: purrr
    ## Loading tidyverse: dplyr

    ## Conflicts with tidy packages ----------------------------------------------

    ## filter(): dplyr, stats
    ## lag():    dplyr, stats

``` r
library(stringr)
library(knitr)

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
}

error_data <- 
  read_tsv('/Users/Poorna/Desktop/Box Sync/Gendermeme/gendermeme/annotated/manual/ann_dump_Fri_May_19_00_59_45_2017.tsv')
```

    ## Parsed with column specification:
    ## cols(
    ##   art_id = col_character(),
    ##   url = col_character(),
    ##   name = col_character(),
    ##   where = col_character(),
    ##   m_gender = col_character(),
    ##   a_gender = col_character(),
    ##   m_count = col_integer(),
    ##   a_count = col_integer(),
    ##   m_quotes = col_integer(),
    ##   a_quotes = col_integer()
    ## )

PRECISION AND RECALL FOR PERSON IDENTIFICATION
----------------------------------------------

``` r
error_data <-
  error_data %>% 
  filter(!(a_gender == "non-living" & where == "auto_only")) %>%
  filter(!(a_gender == "non-living" & str_detect(m_gender, "company"))) %>% 
  filter(!(where == "manual_only" & str_detect(m_gender, "company"))) %>% 
  filter(!(str_detect(name, "(anonymous)|(unnamed)|(unknown)"))) %>% 
  mutate(outlet = map_chr(url, return_outlet))
```

The error rates for people-detection are below:

``` r
error_data %>% 
  group_by(outlet) %>% 
  mutate(n_articles = n_distinct(art_id)) %>% 
  count(n_articles, where) %>% 
  spread(key = where, value = n) %>% 
  ungroup() %>% 
  mutate(precision = both / (auto_only + both), recall = both / (both + manual_only)) %>% 
  arrange(desc(n_articles)) %>% 
  kable()
```

| outlet          |  n\_articles|  auto\_only|  both|  manual\_only|  precision|     recall|
|:----------------|------------:|-----------:|-----:|-------------:|----------:|----------:|
| NYT             |           49|          51|   340|            11|  0.8695652|  0.9686610|
| TechCrunch      |           19|          23|    42|             3|  0.6461538|  0.9333333|
| Washington Post |           10|          10|    78|             2|  0.8863636|  0.9750000|
| Bloomberg       |            1|           3|    10|             2|  0.7692308|  0.8333333|
| LA Times        |            1|           1|    17|            NA|  0.9444444|         NA|

We now examine the error rates for gender detection.

RECALL FOR GENDER
-----------------

First, let us look at those cases where a person was identified by automatically as well as manually. We restrict our attention to people who were identified as either `male` or `female`.

``` r
error_data %>% 
  filter(where == "both", m_gender %in% c("male", "female")) %>% 
  count(m_gender, a_gender) %>% 
  group_by(m_gender) %>% 
  summarize(
    total = sum(n), 
    a_correct = sum(n[a_gender == m_gender]), 
    a_incorrect_none = sum(n[a_gender == "None"]),
    a_incorrect_opp_gender = sum(n[m_gender != a_gender & a_gender %in% c("male", "female")]),
    a_incorrect_non_living = sum(n[m_gender != a_gender & a_gender == "non-living"])
  ) %>% 
  mutate(
    perc_a_correct = a_correct * 100 / total,
    perc_a_incorrect_none = a_incorrect_none * 100 / total,
    perc_a_incorrect_opp_gender = a_incorrect_opp_gender * 100 / total,
    perc_a_incorrect_non_living = a_incorrect_non_living * 100 / total
  ) %>% 
  kable()
```

| m\_gender |  total|  a\_correct|  a\_incorrect\_none|  a\_incorrect\_opp\_gender|  a\_incorrect\_non\_living|  perc\_a\_correct|  perc\_a\_incorrect\_none|  perc\_a\_incorrect\_opp\_gender|  perc\_a\_incorrect\_non\_living|
|:----------|------:|-----------:|-------------------:|--------------------------:|--------------------------:|-----------------:|-------------------------:|--------------------------------:|--------------------------------:|
| female    |    119|         113|                   2|                          3|                          1|          94.95798|                  1.680672|                         2.521008|                        0.8403361|
| male      |    358|         328|                  15|                         15|                          0|          91.62011|                  4.189944|                         4.189944|                        0.0000000|

We find that a lot of men are being mis-tagged as women. Why is this?

Let's have a look at men who are tagged as women.

``` r
error_data %>% 
  filter(where == "both", m_gender == "male", a_gender == "female") %>% 
  select(art_id, outlet, everything(), -url) %>% 
  kable()
```

| art\_id | outlet          | name                   | where | m\_gender | a\_gender |  m\_count|  a\_count|  m\_quotes|  a\_quotes|
|:--------|:----------------|:-----------------------|:------|:----------|:----------|---------:|---------:|----------:|----------:|
| a022    | NYT             | Jamie Vardy            | both  | male      | female    |         2|         2|          0|          0|
| a027    | NYT             | Marin Cilic            | both  | male      | female    |         1|         1|          0|          0|
| a053    | NYT             | Xi Jinping             | both  | male      | female    |         1|         1|          0|          0|
| a053    | NYT             | Donald Trump Jr.       | both  | male      | female    |         1|         2|          0|          0|
| a056    | NYT             | Reagan                 | both  | male      | female    |         1|         1|          0|          0|
| a043    | NYT             | Kim Yoo-na             | both  | male      | female    |         1|         1|         33|         41|
| a069    | NYT             | Kim Sang-duk           | both  | male      | female    |         1|         1|          0|          0|
| a069    | NYT             | Kim Dong-chul          | both  | male      | female    |         1|         1|          0|          0|
| a069    | NYT             | Kim Jong-il            | both  | male      | female    |         1|         1|          0|          0|
| a069    | NYT             | Kim Hak-song           | both  | male      | female    |         2|         2|          0|          0|
| a077    | Washington Post | Gale Buchanan          | both  | male      | female    |         1|         1|          0|          0|
| a078    | Washington Post | Mischa Popoff          | both  | male      | female    |         1|         1|         20|         23|
| a080    | Washington Post | Jan Gaspers            | both  | male      | female    |         1|         1|          0|          0|
| a091    | LA Times        | Lenore Albert-Sheridan | both  | male      | female    |         1|         1|          0|          0|
| a092    | Bloomberg       | Alexis Kohler          | both  | male      | female    |         1|         1|          0|          0|

Let's also look at men who are tagged as "None":

``` r
error_data %>% 
  filter(where == "both", m_gender == "male", a_gender == "None") %>% 
  select(art_id, outlet, everything(), -url) %>% 
  kable()
```

| art\_id | outlet          | name               | where | m\_gender | a\_gender |  m\_count|  a\_count|  m\_quotes|  a\_quotes|
|:--------|:----------------|:-------------------|:------|:----------|:----------|---------:|---------:|----------:|----------:|
| a016    | TechCrunch      | Jean-Claude Biver  | both  | male      | None      |         1|         1|         88|          0|
| a034    | NYT             | Trump              | both  | male      | None      |         1|         1|          0|          0|
| a039    | TechCrunch      | Urs Hlzle          | both  | male      | None      |         2|         2|          9|          0|
| a053    | NYT             | H. R. McMaster     | both  | male      | None      |         1|         1|          0|          0|
| a056    | NYT             | Trump              | both  | male      | None      |         1|         1|          0|          0|
| a056    | NYT             | Tiff Macklem       | both  | male      | None      |         1|         1|         20|         21|
| a058    | NYT             | Trump              | both  | male      | None      |         1|         1|          0|          0|
| a064    | NYT             | Trump              | both  | male      | None      |         2|         2|          0|          0|
| a066    | NYT             | J. Timothy DiPiero | both  | male      | None      |         1|         1|         19|          0|
| a068    | NYT             | Sediqullah Khan    | both  | male      | None      |         2|         1|         49|          0|
| a068    | NYT             | Rahatullah         | both  | male      | None      |         1|         2|          9|          0|
| a078    | Washington Post | Chenglin Liu       | both  | male      | None      |         1|         1|         21|         11|
| a080    | Washington Post | S. Frederick Starr | both  | male      | None      |         1|         1|          0|          3|
| a080    | Washington Post | Narendra Modi      | both  | male      | None      |         1|         1|          0|          0|
| a084    | Washington Post | Trump              | both  | male      | None      |         1|         1|          0|          0|

We find that, quite frequently, "Trump" is being tagged as male by us and as "None" by the computer. We suspect that this is because "Trump" appears in contexts like "Trump administration", only once in the article, etc. A rule might be able to fix this issue.

Let us look at the gender-related accuracy once again:

``` r
error_data %>% 
  filter(outlet %in% c("NYT", "Washington Post", "TechCrunch")) %>% 
  filter(where == "both", m_gender %in% c("male", "female")) %>% 
  group_by(outlet) %>% 
  count(m_gender, a_gender) %>% 
  group_by(outlet, m_gender) %>% 
  summarize(
    total = sum(n), 
    a_correct = sum(n[a_gender == m_gender]), 
    a_incorrect_none = sum(n[a_gender == "None"]),
    a_incorrect_opp_gender = sum(n[m_gender != a_gender & a_gender %in% c("male", "female")]),
    a_incorrect_non_living = sum(n[m_gender != a_gender & a_gender == "non-living"])
  ) %>% 
  mutate(
    perc_a_correct = a_correct * 100 / total,
    perc_a_incorrect_none = a_incorrect_none * 100 / total,
    perc_a_incorrect_opp_gender = a_incorrect_opp_gender * 100 / total,
    perc_a_incorrect_non_living = a_incorrect_non_living * 100 / total
  ) %>% 
  ungroup() %>% 
  kable()
```

| outlet          | m\_gender |  total|  a\_correct|  a\_incorrect\_none|  a\_incorrect\_opp\_gender|  a\_incorrect\_non\_living|  perc\_a\_correct|  perc\_a\_incorrect\_none|  perc\_a\_incorrect\_opp\_gender|  perc\_a\_incorrect\_non\_living|
|:----------------|:----------|------:|-----------:|-------------------:|--------------------------:|--------------------------:|-----------------:|-------------------------:|--------------------------------:|--------------------------------:|
| NYT             | female    |     94|          90|                   2|                          2|                          0|          95.74468|                  2.127660|                         2.127660|                         0.000000|
| NYT             | male      |    246|         227|                   9|                         10|                          0|          92.27642|                  3.658537|                         4.065041|                         0.000000|
| TechCrunch      | female    |      5|           5|                   0|                          0|                          0|         100.00000|                  0.000000|                         0.000000|                         0.000000|
| TechCrunch      | male      |     33|          31|                   2|                          0|                          0|          93.93939|                  6.060606|                         0.000000|                         0.000000|
| Washington Post | female    |     14|          12|                   0|                          1|                          1|          85.71429|                  0.000000|                         7.142857|                         7.142857|
| Washington Post | male      |     58|          51|                   4|                          3|                          0|          87.93103|                  6.896552|                         5.172414|                         0.000000|

Note that this is a slightly strange, and over-optimistic, metric. We are isolating only those people that WERE identified as people, and among those, finding the recall for gender. However, some male and female people fall out of the pipeline at the person-detection stage, so the above recall numbers are slightly inflated. Let's correct for this.

``` r
error_data %>% 
  filter(
    outlet %in% c("NYT", "TechCrunch", "Washington Post"), 
    m_gender %in% c("male", "female"), 
    (where == "manual_only" | where == "both")
  ) %>% 
  group_by(outlet) %>% 
  count(m_gender, a_gender) %>% 
  mutate(a_gender = ifelse(is.na(a_gender), "person not identified", a_gender)) %>% 
  group_by(outlet, m_gender) %>% 
  summarize(
    total = sum(n), 
    a_correct = sum(n[a_gender == m_gender]), 
    a_incorrect_none = sum(n[a_gender == "None"]),
    a_incorrect_opp_gender = sum(n[m_gender != a_gender & a_gender %in% c("male", "female")]),
    a_incorrect_non_living = sum(n[m_gender != a_gender & a_gender == "non-living"]),
    a_person_not_identified = sum(n[m_gender != a_gender & a_gender == "person not identified"])
  ) %>% 
  mutate(
    perc_a_correct = a_correct * 100 / total,
    perc_a_incorrect_none = a_incorrect_none * 100 / total,
    perc_a_incorrect_opp_gender = a_incorrect_opp_gender * 100 / total,
    perc_a_incorrect_non_living = a_incorrect_non_living * 100 / total,
    perc_a_person_not_identified = a_person_not_identified * 100 / total
  ) %>% 
  ungroup() %>% 
  kable()
```

| outlet          | m\_gender |  total|  a\_correct|  a\_incorrect\_none|  a\_incorrect\_opp\_gender|  a\_incorrect\_non\_living|  a\_person\_not\_identified|  perc\_a\_correct|  perc\_a\_incorrect\_none|  perc\_a\_incorrect\_opp\_gender|  perc\_a\_incorrect\_non\_living|  perc\_a\_person\_not\_identified|
|:----------------|:----------|------:|-----------:|-------------------:|--------------------------:|--------------------------:|---------------------------:|-----------------:|-------------------------:|--------------------------------:|--------------------------------:|---------------------------------:|
| NYT             | female    |     97|          90|                   2|                          2|                          0|                           3|          92.78351|                  2.061856|                         2.061856|                         0.000000|                          3.092783|
| NYT             | male      |    254|         227|                   9|                         10|                          0|                           8|          89.37008|                  3.543307|                         3.937008|                         0.000000|                          3.149606|
| TechCrunch      | female    |      5|           5|                   0|                          0|                          0|                           0|         100.00000|                  0.000000|                         0.000000|                         0.000000|                          0.000000|
| TechCrunch      | male      |     36|          31|                   2|                          0|                          0|                           3|          86.11111|                  5.555556|                         0.000000|                         0.000000|                          8.333333|
| Washington Post | female    |     14|          12|                   0|                          1|                          1|                           0|          85.71429|                  0.000000|                         7.142857|                         7.142857|                          0.000000|
| Washington Post | male      |     59|          51|                   4|                          3|                          0|                           1|          86.44068|                  6.779661|                         5.084746|                         0.000000|                          1.694915|

This table gives us true recall for genders. We probably need more data for Washington Post.

PRECISION FOR GENDER
--------------------

Let's see what our precision is for genders. That is, when we say someone is male, how often are they really male? Or when we say someone is female, how often are they really female? This should (hopefully) be easy to find.

``` r
error_data %>% 
  filter(
    (where == "auto_only" | where == "both"),
    outlet %in% c("NYT", "Washington Post", "TechCrunch"),
    a_gender %in% c("male", "female")
  ) %>% 
  group_by(outlet) %>% 
  count(a_gender, m_gender) %>% 
  mutate(m_gender = ifelse(is.na(m_gender), "not a person", m_gender)) %>% 
  group_by(outlet, a_gender) %>% 
  summarize(
    total = sum(n),
    correct = sum(n[a_gender == m_gender]),
    true_gender_opposite = sum(n[m_gender != a_gender & m_gender %in% c("male", "female")]),
    not_a_person = sum(n[m_gender == "not a person"])
  ) %>% 
  mutate(
    precision = correct * 100 / total,
    true_gender_opp_perc = true_gender_opposite * 100 / total,
    not_a_person_perc = not_a_person * 100 / total
  ) %>% 
  ungroup() %>% 
  kable()
```

| outlet          | a\_gender |  total|  correct|  true\_gender\_opposite|  not\_a\_person|  precision|  true\_gender\_opp\_perc|  not\_a\_person\_perc|
|:----------------|:----------|------:|--------:|-----------------------:|---------------:|----------:|------------------------:|---------------------:|
| NYT             | female    |    111|       90|                      10|              11|   81.08108|                9.0090090|              9.909910|
| NYT             | male      |    252|      227|                       2|              23|   90.07937|                0.7936508|              9.126984|
| TechCrunch      | female    |      7|        5|                       0|               2|   71.42857|                0.0000000|             28.571429|
| TechCrunch      | male      |     44|       31|                       0|              12|   70.45455|                0.0000000|             27.272727|
| Washington Post | female    |     17|       12|                       3|               1|   70.58824|               17.6470588|              5.882353|
| Washington Post | male      |     57|       51|                       1|               3|   89.47368|                1.7543860|              5.263158|

Precision is not as good as recall. This is a little worrying: if recall was about the same for each gender, but precision were really high, we'd still have a good tool. If recall is high, but precision is low, we're not in good shape.
