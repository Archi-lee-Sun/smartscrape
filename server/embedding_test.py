from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

# Pair 1: TRUE DUPLICATE — same Privacy Talks episode, two different Oasis channels
oasis_1 = "New episode of Privacy Talks is out now! The biggest month in crypto and AI yet, all in one episode. We break down the DeFi collapse that wiped out 40+ protocols and over $770M, the AI layoff wave reshaping Big Tech, Google's bet on agents, and a record month for Anthropic and OpenAI."
oasis_2 = "Have you checked out the latest episode of Privacy Talks yet? Tune in as we break down: The DeFi collapse that impacted 40+ protocols and led to over $770M in losses, The AI layoff wave reshaping Big Tech, Google's push into AI agents, A record-setting month for Anthropic and OpenAI."

# Pair 2: RELATED BUT NOT DUPLICATE — same transfer saga, different moment/certainty
lee_1 = "Kang-in Lee to Atletico Madrid, here we go! Deal in place between all parties. Deal worth around 40m euros from PSG."
lee_2 = "The plan remains clear: Kang-in Lee to Atletico Madrid and PSG advancing to get Maghnes Akliouche."

# Pair 3: BASELINE UNRELATED — different topics entirely
rock = "Iron Maiden will finish filming a concert movie of their current Run For Your Lives tour at their own Eddfest festival, happening July 10-11 at the legendary Knebworth venue in the UK."
football = "Understand Jeremy Monga undergoes his medical as new Manchester City player today. Deal done with Leicester since last week for fee around 10m pounds."

embeddings = model.encode([oasis_1, oasis_2, lee_1, lee_2, rock, football])

sim_oasis = util.cos_sim(embeddings[0], embeddings[1])
sim_lee = util.cos_sim(embeddings[2], embeddings[3])
sim_baseline = util.cos_sim(embeddings[4], embeddings[5])

print(f"TRUE DUPLICATE (Oasis Privacy Talks):    {sim_oasis.item():.4f}")
print(f"RELATED, NOT DUPLICATE (Kang-in Lee):     {sim_lee.item():.4f}")
print(f"UNRELATED BASELINE (rock vs football):    {sim_baseline.item():.4f}")