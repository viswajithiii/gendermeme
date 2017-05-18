library(babynames)
library(tidyverse)

babynames.summary <-
  babynames %>% 
  group_by(name, sex) %>% 
  summarize(count = sum(n)) %>%   
  ungroup() %>% 
  spread(key = sex, value = count, fill = 0)  %>% 
  rename(male = M, female = F) %>% 
  mutate(
    male = male + 1,
    female = female + 1,
    total = male + female
  ) %>% 
  arrange(desc(total)) %>% 
  mutate(
    ratio = ifelse(male > female, female / male, male / female)
  ) 

babynames.summary %>% 
  ggplot() +
  geom_histogram(aes(x = ratio), binwidth = 0.005)

# If ratio < 0.02, gender is 'certain'. Else, gender is a tuple.
MAX_CERTAIN_RATIO = 0.025

babynames.summary <-
  babynames.summary %>% 
  mutate(
    majority = ifelse(male > female, 'male', 'female'),
    minority = ifelse(male > female, 'female', 'male'),
    certainty = ifelse(ratio < MAX_CERTAIN_RATIO, 'yes', 'no')
    ) 

setwd('/Users/Poorna/Desktop/Box Sync/Gendermeme/gendermeme/analysis')
fileGender <- 'gender_babynames.py'
write("gender = {", fileGender)

for (i in 1:nrow(babynames.summary)){
  name = babynames.summary[i, ]$name
  certainty = babynames.summary[i, ]$certainty
  majority = babynames.summary[i, ]$majority
  minority = babynames.summary[i, ]$minority
  if (certainty == "yes"){
    gender = paste0("'",majority,"'")
  } else {
    gender = paste0("('", majority, "', '", minority, "')")
  }
  write(paste0("u'", toupper(name), "': ", gender, ","), fileGender, append = TRUE)
  if (i %% 500 == 0) {
    print(paste0("Iteration:", i))
  }
}

write("}", fileGender, append = TRUE)

