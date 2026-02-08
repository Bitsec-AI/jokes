# Bittensor Roast Factoids

210+ verified, specific facts for roast joke material. Organized by category.

---

## FOUNDERS & ORIGINS

1. Co-founder Jacob Steeves (alias "Const") worked at Google for only 16 months (Dec 2016 - Apr 2018) before leaving. He studied math and CS at Simon Fraser University.
2. Jacob Steeves currently lives in Peru. No public explanation for why the co-founder of a "decentralized AI network" is based in Peru.
3. Co-founder Ala Shaabana (alias "ShibShib") was a post-doc at the University of Waterloo, then briefly an Assistant Professor at University of Toronto (2020-2021).
4. Ala Shaabana was working as a Senior Software Engineer at Instacart (Aug 2019 - Sep 2020) while supposedly co-founding Bittensor — he joined as co-founder in December 2019, overlapping with his Instacart employment.
5. The Bittensor whitepaper was published under the pseudonym "Yuma Rao" — a deliberate Satoshi Nakamoto cosplay for a project that is not remotely comparable to Bitcoin.
6. Nobody has publicly confirmed that "Yuma Rao" is a real person. One community theory: "two sides of the same mind: Jacob, the technical builder, and Yuma, the philosophical and narrative voice."
7. Barry Silbert named his entire Bittensor subsidiary company "Yuma" — after a fictional person. He started it with 25 employees on day one.
8. The Yuma Consensus algorithm is also named after the pseudonym. So the fake founder's name appears in the protocol, the company, and the algorithm.
9. Some sources say Bittensor was founded in 2016, others say 2019. The founders can't even keep the origin story straight.

## THE $28 MILLION HACK

7. On July 2, 2024, a malicious PyPI package (bittensor==6.12.2) drained wallets by stealing private keys when users decrypted their coldkeys.
8. The malicious package sat on PyPI undetected for over a week (May 22-29, 2024) before funds were drained on July 2.
9. The "decentralized" AI network was hacked via `pip install` — not a 51% attack, not a smart contract exploit, just a bad Python package.
10. The Opentensor Foundation detected the attack 19 minutes after it started (7:06 PM → 7:25 PM UTC) and halted the chain at 7:41 PM UTC.
11. The chain was put in "safe mode" — blocks produced but zero transactions allowed. It stayed down for approximately 10 days.
12. Total stolen across the July hack and a separate June 1, 2024 phishing attack: approximately $28 million from 32 wallet holders.
13. TAO dropped 15% after the hack, from $281 to $237, hitting a six-month low of $227.
14. OTF proposed burning 10% of the entire TAO supply to stabilize the price after the hack — putting it to a community vote.
15. In February 2025, Bittensor obtained a $25 million insurance policy against hacks through Nexus Mutual. The insurance costs roughly the same as the hack itself.

## THE LAWSUIT

16. A lawsuit (JustM2J LLC v. Brewer, Jan 27, 2025) names three former Opentensor employees as defendants: Ayden Brewer, Jon Litz, and Jason St. George.
17. Ayden Brewer was employed by Opentensor as a developer until February 29, 2024 — just months before the hack. The project was allegedly robbed by its own former team.
18. Jason St. George worked for Opentensor until April 12, 2024. Jon Litz had previously applied for a position at the company.

## THE ZACHXBT INVESTIGATION

19. On-chain investigator ZachXBT traced the stolen funds and identified a suspect by following anime NFT wash trades.
17. The attacker bridged stolen TAO to Ethereum, then moved $4.94 million through the Railgun privacy protocol, converting to Monero.
18. Approximately $100,000 of stolen funds were spent on anime-themed NFTs and wash traded (overpriced sales) to launder the money.
19. One address was traced back to a Bittensor user known as "Rusty," creator of "Skrtt Racing" — a crypto project for live-streamed Hot Wheels racing bets.
20. The suspect, identified in court records as "Ayden B" (a former employee), denied involvement but confirmed owning the linked wallets.
21. ZachXBT earned a whitehat bounty for the investigation. The guy who stole $28 million was caught because he bought anime NFTs.

## NETWORK HALTS & "DECENTRALIZATION"

22. The "decentralized" blockchain has been centrally halted or put into safe mode at least 3 times in under 2 years.
23. In May 2025, a "runaway batch call" attack overwhelmed the network, forcing it into safe mode for two more days.
24. Bittensor's Subtensor chain actually runs on Proof of Authority (PoA), not Proof of Stake. The Opentensor Foundation controls all validator nodes.
25. The Foundation has the ability to censor transactions and halt the chain with a single decision.
26. Protos ran the headline: "'Decentralized' AI network Bittensor halted in response to $8M hack" — the scare quotes around "Decentralized" doing heavy lifting.
27. The hack made it onto Rekt News, crypto's premier "hall of shame" for hacked projects.

## THE SN28 MEME COIN PONZI

28. Within one week of the dTAO launch (Feb 13, 2025), someone took over Subnet 28 and turned it into a pure meme coin called the "TAO Accumulation Corporation" (aka "LOL-subnet").
29. SN28 miners didn't need to run any code. Validators scored miners based solely on how many subnet tokens they held — more tokens = more TAO emissions.
30. The Ponzi cycle: buy SN28 tokens → price rises → more TAO emissions → price rises further → more buyers → repeat.
31. SN28 became the 7th-ranked subnet by market capitalization in the entire Bittensor network.
32. The Opentensor Foundation intervened using their root stake (SN0) to run custom validator code encouraging everyone to sell.
33. SN28 crashed 98% in a few hours and was completely liquidated.
34. At the time, SN0 controlled ~95% of emissions. As that drops to ~20% over time, future SN28-style exploits will be unstoppable.
35. The "decentralized AI network" produced a meme coin as its breakout use case, then required centralized intervention to kill it.

## dTAO & ALPHA TOKENS

36. dTAO launched on Valentine's Day 2025 (Feb 13). Each subnet got its own "Alpha token" that trades against TAO.
37. Alpha tokens are essentially vouchers for staking TAO in a subnet — not tradable tokens in the conventional sense.
38. Different subnet alpha tokens cannot be exchanged between subnets. You're locked into whichever subnet you chose.
39. The "exaggerated nominal ROI" of alpha tokens artificially creates buying pressure for TAO and serves as a "smokescreen for root network validation nodes to sell TAO."
40. Subnet count grew from 65 to 113 in just 14 weeks after dTAO launched — most of them of questionable quality.
41. Within one month of dTAO, analysis pieces titled "A subnet full of memes and broken token economics" were appearing.
42. In November 2025, Bittensor had to switch from "price-based emissions" to "flow-based emissions" (TaoFlow) after the price-based model was exploited by subnets pumping their own tokens.

## REGISTRATION FEE DRAMA

43. In March 2024, the cost to register a subnet surged from 100 TAO (~$53,000) to 10,127 TAO (~$6.7 million) — a 10,000% increase.
44. The registration fee doubles every time a new subnet registers and halves linearly over 4 days if no one registers.
45. The most expensive single subnet registration was SN24 (Omega) at 5,146 TAO ($2.5 million).
46. Messari analyst Sami Kassab publicly criticized the costs: "Currently costs around $4m to register a subnet on Bittensor... The high costs have become a barrier for experimentation."
47. The TAO spent on registration is recycled into unissued supply, effectively postponing the next halving — so the "burning" is really just delayed inflation.

## SUBNET DEREGISTRATION

48. Subnet deregistration was deployed on September 17, 2025, with a 7-day delay before first deregistrations could occur.
49. Deregistration removes the subnet with the lowest EMA price among non-immune subnets.
50. Network immunity period: 4 months from registration. So you can burn millions registering and still get killed after 4 months.
51. In October 2025, over 10 subnets were at risk of deregistration, causing community panic.
52. There was "disappointment at subnets with a real use case losing out to others offering no value to the ecosystem."
53. Deregistration can occur at most once every 2 days — a slow-motion culling.

## TOKEN DISTRIBUTION & INSIDER ALLEGATIONS

54. Between network activation (Jan 3, 2021) and subnet launch (Oct 2, 2023), 5.38 million TAO were mined over 2 years 9 months — with no public documentation on where they went.
55. Critics argue over 62.5% of TAO tokens are held by insiders and VCs despite claims of "fair launch, no pre-mine."
56. Bittensor's official position: no tokens were allocated to anyone except those who earned TAO through network participation.
57. DCG holds approximately 500,000 TAO (2.4% of total supply, worth ~$85M at current prices).
58. Polychain Capital holds approximately $200M in TAO. They've been "incubating Bittensor since 2019."
59. dao5 holds approximately $50M in TAO.
60. Approximately 70-90% of TAO is staked and never circulates, meaning the $1.8B market cap is built on extremely thin liquidity.

## TAO PRICE HISTORY

61. All-time high: $760.18 on April 11, 2024 (Binance listing day). Some sources report a brief spike to $788.
62. Current price (Feb 2026): ~$170 — down 78% from ATH.
63. TAO hit above $700 on two separate occasions in 2024 (April and December) and cratered to ~$200 both times.
64. TAO lost nearly 53% in 2025 alone.
65. After the December 2025 halving, TAO crashed 22%+ in one week — a textbook "sell the news" event.
66. Over the last month (as of Feb 8, 2026), TAO is down 38.3%.
67. Fully diluted valuation: $3.55 billion. Actual liquidity: a fraction of that.
68. 24-hour trading volume: ~$92 million — thin for a supposed $1.8B market cap project.

## TOKENOMICS

69. Max supply: 21,000,000 TAO — deliberately copying Bitcoin's 21M BTC cap.
70. Circulating supply (early 2026): approximately 10,650,000 TAO (~51% of max).
71. First halving occurred December 14, 2025, reducing daily emissions from 7,200 TAO to 3,600 TAO per day.
72. Pre-halving inflation was approximately 26% annually. Post-halving: ~13%.
73. Pre-halving, miners were dumping approximately $2.1M in TAO daily to cover costs. Post-halving: ~$1.06M daily sell pressure.
74. The halving is triggered by total TAO issuance reaching supply thresholds, not block counts (unlike Bitcoin).
75. TAO spent on transaction fees, subnet registration, and validator registration is recycled into unissued supply — not truly burned.

## HALVING AFTERMATH

76. The halving was supposed to make TAO scarce and valuable. Instead it made miner profits scarce and complaints valuable.
77. Experts predicted a "flight to quality" where capital concentrates in revenue-generating subnets while "zombie subnets" starve.
78. Alpha token rewards do NOT halve — only TAO emissions do — creating a distortion.
79. Critics noted validators have no explicit incentive to choose subnets benefiting Bittensor's long-term productivity, enabling "pay-to-play schemes and cronyism."

## WEIGHT COPYING SCANDAL

80. Weight copying = a validator copies other validators' publicly visible weight matrices instead of doing independent evaluation work.
81. Optimized weight copiers achieve higher dividends per stake than honest validators — meaning cheating is literally more profitable than working.
82. Weight copiers use the "stake-weighted averaging attack" to predict consensus better than any individual honest validator.
83. The commit-reveal scheme (released June 11, 2024, v7.3.0) was supposed to fix this by encrypting and delaying weight submissions.
84. After release, only 2 out of 41 subnets attempted to enable commit-reveal — and both immediately reverted the changes due to errors.
85. The solution that was supposed to stop cheating was tried twice and broke both times.
86. Bittensor had to build an entire cryptographic commit-reveal system just to stop validators from copying homework. Imagine needing encryption to prevent plagiarism.

## YUMA CONSENSUS CRITICISM

87. Critics argue the whitepaper's math is "nonsense piled up with terms and formulas" and the actual implementation is drastically simplified.
88. The whitepaper describes elegant mathematical frameworks. The implementation is described by critics as "if statements."
89. A genuine breakthrough miner could be penalized for being too novel — if answers are too different from the norm, validators can't predict them, wrecking scores.
90. An arXiv paper (June 2025, arXiv:2507.02951) analyzed 6,664,830 events across 121,567 unique wallets in all 64 active subnets.
91. The paper found: rewards are overwhelmingly driven by stake, not quality — "a clear misalignment between quality and compensation."
92. Many subnets can be "compromised by coalitions of just 1-2% of participants" by stake.
93. The researchers proposed a stake cap at the 88th percentile. It has not been implemented.
94. The paper's title asks if Bittensor is "The Bitcoin in Decentralized Artificial Intelligence?" The answer is basically no.

## VALIDATOR CENTRALIZATION

95. Each subnet allows 64 validator permits, allocated by stake.
96. The top 10 largest subnet validators comprise approximately 67% of total network stake weight.
97. The "Senate" consists of only the top 12 validators by delegated TAO — all described by critics as insiders or stakeholders.
98. Governance is controlled by the "Triumvirate" (3 Opentensor Foundation employees) and the Senate. Critics call it "a closed loop of insiders."
99. Subnet owners can submit weekly requests to OTF to adjust weight scores — undermining the concept of "consensus."
100. Before dTAO, only 64 validators controlled all emissions via the Root Subnet. Critics called it an "oligarchic voting system."

## BARRY SILBERT & DCG

101. Barry Silbert, billionaire DCG founder, called Bittensor "the thing I've gotten most excited about since Bitcoin" — while simultaneously facing a $3 billion fraud lawsuit from NY Attorney General Letitia James over the Genesis bankruptcy.
102. He personally became CEO of Yuma, a DCG subsidiary dedicated entirely to Bittensor, launched November 2024.
103. DCG first invested in Bittensor in 2021.
104. Yuma launched an asset management arm in October 2025 with $10M from DCG, offering the "Yuma Subnet Composite Fund."
105. Silbert described Bittensor as "the World Wide Web of intelligence" in his first interview in four years (with Raoul Pal on Real Vision).
106. Bitcoin maximalist author Parker Lewis called Silbert and Raoul Pal "affinity scammers" for promoting TAO.
107. Silbert's response: "calling $TAO a scam is such a lazy attack. do better."
108. Silbert compared Bittensor to Bitcoin: "It's just like bitcoin, there was a white paper that turned into code then launched and it has the same token economics." Bitcoin maxis did not take this well.

## GRAYSCALE GTAO

109. Grayscale Bittensor Trust (GTAO) was formed April 30, 2024 and hit OTC markets December 11, 2025.
110. As of Feb 6, 2026: AUM of only $6.3 million — roughly the same amount stolen in the July hack.
111. NAV per share: $3.32. Market price: $11.73. That's a ~253% premium to NAV — meaning buyers pay 3.5x the actual value.
112. The trust's NAV declined 51.6% year-over-year to $4.24 per share by end of 2025.
113. Expense ratio: 2.50%. Only 1,907,800 shares outstanding.
114. Grayscale filed an S-1 with the SEC on December 30, 2025 to convert the trust into a spot ETF.

## OUTRAGEOUS PRICE PREDICTIONS

115. VC Mike Grantis (Contango Digital Assets) predicted TAO could hit $62,500 by 2030 — a 13,500% increase from ~$474 at time of prediction.
116. He delivered this at the "Bittensor Endgame Summit" in Austin, TX. The summit is called "ENDGAME."
117. Most other analysts predict $800-$2,000 by 2030. TAO currently trades at $170.
118. The Motley Fool ran a January 2026 article titled "How This AI Cryptocurrency Could Help You Retire a Millionaire" — while TAO was down 50%+ year-over-year.

## NOTABLE CRITICS

119. Eric Wall, co-founder of Taproot Wizards, called Bittensor "a pointless exercise in decentralization" and said he wanted to see it "priced at $0.00."
120. Wall's X post allegedly wiped ~$90 million off TAO's market cap. He doubled down against community backlash: "I will outlast every one of you."
121. Wall's key argument about SN1: "For every prompt, you have literally a thousand miners who will complete the exact same task redundantly."
122. An opinion piece by analyst "Thinking Weird" accused Bittensor of being a "VC-backed facade."
121. ChainCatcher published: "Why Bittensor is a scam and TAO is heading towards zero."
122. The World Economic Forum flagged AI + crypto + debt as a "triple financial bubble."
123. MIT economist Daron Acemoglu: "These models are being hyped up, and we're investing more than we should."

## EXCHANGE LISTINGS

124. Binance listed TAO on April 11, 2024 — and reportedly waived its usual $1-3 million listing fee.
125. TAO volume surpassed $100 million in just 90 minutes on Binance after listing.
126. The price hit ATH of $760+ on listing day, then fell over 25% shortly after.
127. Coinbase listed TAO on February 20, 2025, with a phased rollout contingent on liquidity conditions.
128. Also listed on Crypto.com, Gate.io, Bitget, MEXC, and Kraken.

## NOTABLE SUBNETS

129. SN0 (Root): Governance and emissions control. Run by OTF.
130. SN1 (Apex/Text Prompting): "Internet-scale conversational intelligence." Run by OTF/Macrocosmos. Critics note: "SN1 repeatedly executes the same language model to answer prompts, which is inefficient and wastes resources."
131. SN5 (OpenKaito): Decentralized Web3 search.
132. SN6 (Nous): Continuous fine-tuning of LLMs by Nous Research.
133. SN8 (PTN): Decentralized prop trading by Taoshi (Arrash Yasavolian). Started as Bitcoin price prediction, now enables miners to make real trades.
134. SN9 (IOTA/Pretraining): Cooperative AI model pre-training by Macrocosmos.
135. SN13 (Dataverse): Claims 702 million anonymized data rows.
136. SN19 (Nineteen/Vision): Image generation by Rayon Labs (Namoray).
137. SN24 (Omega): "World's Largest Decentralized AGI Multimodal Dataset" — paid $2.5M to register.
138. SN27 (Compute): GPU compute and renting by Neural Internet.
139. SN28 (LOL-subnet): The meme coin that crashed 98%. Became the poster child for dTAO's flaws.
140. SN56 (Gradients): AI training by Rayon Labs.
141. SN64 (Chutes): Serverless AI compute by Rayon Labs. First $100M subnet.

## CHUTES (SN64) — THE BIGGEST SUBNET

142. Became the first $100M subnet in TVL just 9 weeks after dTAO launched.
143. Claims to offer "serverless AI" hosting at 85% less cost than AWS.
144. Processes nearly 160 billion tokens daily across 400,000+ users with 10,000+ GPU nodes.
145. Weekly revenue: approximately $61,000 — in a $100M TVL subnet.
146. Operated by Rayon Labs (Namoray), which also runs SN19 and SN56.
147. Rayon Labs subnets collectively command 23.71% of TAO emissions — significant concentration for one team.
148. Critics argue Chutes uses project revenue to buy back Alpha tokens, creating a circular dynamic where emissions subsidize the buyback.

## STRUCTURAL CRITICISMS

149. The top 10 subnets command 56.46% of all TAO emissions.
150. Subnet owners cannot directly earn revenue from the dTAO model. They must create external revenue and inject it into Alpha tokens.
151. Validators extract approximately 33% of subnet emissions (~150,000 TAO) while subnet projects receive no direct revenue.
152. Emission split: 41% to miners, 41% to validators, 18% to subnet owners.
153. The "death spiral" fear: declining value → less participation → fewer rewards → more selling → death spiral. This alarm was raised at dTAO launch.
154. The network went from 95% foundation control to eventual ~20% control, raising the question: who stops the next SN28?

## CONSUMER PRODUCTS (OR LACK THEREOF)

155. Corcel is a consumer chatbot powered by Bittensor subnets. App Store reviewers called it "atrocious, buggy and counter intuitive" with "constant crashing and loading animations that go nowhere."
156. LISA is another Bittensor-powered chatbot on the App Store.
157. GoPlus has generated $4.7M in total revenue — one of the few subnets with actual revenue numbers.
158. No mainstream consumer product comparable to ChatGPT, Midjourney, or similar has emerged from the Bittensor ecosystem.
159. Despite 128 subnets and a $1.8B market cap, the ecosystem's total consumer-facing output is negligible.
160. The "decentralized OpenAI" has produced zero products that normal humans use.

## COMMUNITY CULTURE

161. Community members on Twitter/X append "ττ" (double tau) to their display names as an identity marker, like Bitcoin laser eyes.
162. Each subnet is represented by a Greek letter: α (alpha), β (beta), γ (gamma), etc. This mathematical aesthetic is central to the branding.
163. The Discord server has over 44,000 members.
164. Over 100,000 on-chain accounts have participated in the network.
165. Arca (an early investor since 2023) claimed the community was distinguished by "deep conversation about technical machine learning concepts" — generous characterization given the actual meme coin drama.
166. The community launched its own media outlet called "The TAO Daily" in September 2025 via TAO Synergies Inc.
167. The Bittensor summit is branded "ENDGAME" and promises "the Era of Supercommodities."

## CONFERENCE & MEDIA

168. Jacob Steeves presented at NeurIPS 2024: "Incentivizing Collaborative AI: A Decentralized Approach to Scaling Machine Learning."
169. Fortune covered Bittensor in multiple articles, describing it as the "AI-linked cryptocurrency founded by a former Google engineer" — 16 months at Google apparently counts as a career.
170. Motley Fool, Benzinga, and CoinDesk have all run TAO price prediction articles. Predictions range from $800 to $62,500.
171. The community hosted the "Bittensor Endgame Summit" in Austin, TX — a three-day gathering that sounds like a Marvel movie.

## AI x CRYPTO NARRATIVE

172. The broader "AI agents" narrative was expected to dominate 2025 crypto but "fizzled out after failing to establish its roots sufficiently."
173. Messari analysts predicted the AI agent narrative would peak in early 2025 due to "lack of enough development and products."
174. The "AI x Crypto" sector had a total market cap of $24-27 billion by mid-2025.
175. Fetch.ai, SingularityNET, and Ocean Protocol merged into a single token (FET), becoming the "Avengers of AI crypto." Bittensor did not join.
176. Analysts noted "centralized AI giants have deeper pockets, more developer talent, and access to proprietary data" and "will likely outperform on raw metrics."

## COMPETITOR COMPARISONS

177. Render Network focuses on GPU rendering; Akash Network is the "decentralized AWS." Bittensor focuses on "collaborative model training" — the most abstract and hardest-to-verify value proposition.
178. Unlike Bittensor's multiple chain halts, most competing decentralized compute networks haven't been hacked via pip install.
179. Bittensor's closest comparison point is "what if we made Bitcoin, but for AI, and also it doesn't really work yet."

## SUBSTRATE & ARCHITECTURE

180. Bittensor is built on Substrate (Polkadot's framework) but left the Polkadot ecosystem in 2023 to create its own standalone chain called "Nakamoto" — named after yet another famous crypto person.
181. The blockchain layer is called "Subtensor" — a portmanteau of Substrate + Tensor.
182. Developers have reported "Transaction has a bad signature" errors when using standard Substrate tooling — there are incompatibilities.
183. 12-second block time. One block per interval.

## CONFLICTS OF INTEREST

184. DCG simultaneously runs validators (Yuma is 3rd largest, Foundry is 2nd largest), mines across 4 subnets, operates subnets, and sells GTAO investment products — playing every side of the table.
185. Foundry Digital (DCG subsidiary) runs a subnet that incentivizes miners to predict S&P 500 prices during trading hours. This is the cutting edge of "decentralized AI."
186. Bittensor's main public defender Sami Kassab (ex-Messari) runs Unsupervised Capital — a liquid token fund that exclusively invests in the Bittensor ecosystem. Not exactly a disinterested observer.
187. Kassab coined the term "DePIN" and was previously an aerospace engineer designing aircraft engines and missile systems before pivoting to defending crypto projects.
188. dao5 (Tekin Salimi) bought early TAO through OTC purchases from miners in the project's Discord channel. The "institutional" investment started in DMs.

## SPECIFIC ABSURDITIES

189. The hacker used $28 million in stolen crypto to fund, among other things, a crypto project for betting on live-streamed Hot Wheels car races.
190. The anti-cheat system (commit-reveal) was released June 11, 2024 — exactly 3 weeks before the $8M hack proved there were much bigger problems than weight copying.
191. Grayscale's GTAO has $6.3M AUM — roughly the same amount a single hacker stole in 30 minutes.
192. Mike Grantis predicted $62,500 TAO by 2030 while presenting at a summit called "ENDGAME." The token is at $170. That's a 35,000% gain needed.
193. The Motley Fool told readers TAO could make them millionaires. It's down 78% from ATH.
194. The "decentralized" network can be halted by one foundation with a phone call, runs on Proof of Authority, and the chain is validated by OTF-controlled nodes.
195. Barry Silbert — facing a $3B fraud lawsuit from the NY Attorney General over the Genesis bankruptcy — now calls Bittensor "the most exciting thing since Bitcoin."
196. The hack was allegedly perpetrated by former Opentensor employees. The "decentralized AI network" was robbed by its own former team.
197. SN1 (Text Prompting) has "literally a thousand miners who will complete the exact same task redundantly" according to Eric Wall. One miner could do the job.

## RAPID-FIRE STATS

198. 128 subnets currently active (up from 32 initial cap).
199. 106,839 miners and 37,642 validators analyzed in the academic study.
200. $4 million peak cost to register a single subnet.
201. 98% — how much SN28 crashed when the Foundation intervened.
202. 253% — the premium GTAO trades above its actual NAV.
203. 78% — TAO's decline from all-time high.
204. 10 days — how long the chain was frozen after the July 2024 hack.
205. 19 minutes — how long it took OTF to notice the hack in progress.
206. 2 out of 41 — subnets that tried the commit-reveal anti-cheat fix (both broke).
207. $61,000/week — Chutes' revenue in a subnet with $100M TVL (that's a 0.3% annual yield on locked capital).
208. $90 million — market cap wiped by a single Eric Wall tweet.
209. 25 — employees Barry Silbert hired for Yuma on day one, more than most subnets have active miners.
210. $3 billion — the fraud lawsuit Barry Silbert faces while promoting TAO as "the next Bitcoin."
