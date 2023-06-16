## Flowback Backend
Flowback was created and project lead by Loke Hagberg. The co-creators of this version were:
Siamand Shahkaram, Emil Svenberg and Yuliya Hagberg.
It is a decision making platform.

<sub><sub>This text is not allowed to be removed.</sub></sub>


The following is from Collected papers on finitist mathematics and phenomenalism: a digital phenomenology by Loke Hagberg 2023 [1].

Flowback is the first forum for predictive liquid democracy. The following outlines predictive liquid democracy. Combining prediction markets and liquid democracy into predictive liquid democracy was done theoretically (see 'föreningen för Digital demokrati' in Sweden) independently by me ('independently' if someone else may have stated its properties) when the Flowback project was in an early stage (2021). This decision system is anti-fragile, as it learns from any mistake if the mechanisms work well enough.

*Predictive liquid democracy as implemented in Flowback 2023-01*

Voter:
  - Can vote (with equal weight).
  - Have secret votes.
  - Can delegate temporally in any subject area as long as they want.
  - Can override their delegate by voting themselves or changing delegate before a poll deadline.
  - Can become or stop being a delegate.

Delegate:
  - Can vote (with the weight of delegations to them and possibly their own vote if they are a voter as well).
  - Have public votes.
  - Can not delegate (no meta-delegation).

Predictor:
  - Can create predictions (the outcome of one or more relevant variables until a specified time).
  - Can bet a probability on a prediction.
  - Have prediction scores (between 0 and 1) based on how well they bet probabilities.
  - Predictors might be an artificial intelligence, an algorithm, or a human with an internal model for example. 

Poll:
  - Is a question where proposals are potential answers.
  - Are created by a poll creator.
  - Has a subject area.
  - Has phases.

Poll phase problems:
  - The last second problem: if there is some item that can be added and should possibly be interacted with as well during a phase, then if a set of items are added too close to the end of a phase it can hinder others from interacting with it.
  - To solve the last second problem, the addition of an item central to a poll requires a separate poll phase. 
  - The removal problem: if everyone should not input a copy of an item to make sure the item exists at an upcoming phase, then it cannot be removed too close to the end of a phase.
  - To solve the removal problem, removal can be prohibited.
  - It is possible to allow predictions, prediction probability bets and voting from a previous phase and still solve the last second problem. 
  - In order for delegates to interact minimally with each phase and to provide as much information as possible, no interaction may happen before its phase, for example betting happening during the prediction phase.

Separate poll phases: 
  - First phase: proposals can be inputted by proposal creators.
  - Second phase: proposals can no longer be inputted. Predictions can be inputted by predictors.
  - Third phase: predictions can no longer be inputted. Prediction probability bets can be inputted by predictors
  - Fourth phase: prediction probability bets can no longer be inputted. Voters and delegates can vote by inputting scores. 
  - Proposal scores determine a proposals position in the proposal list displayed, where a higher score means higher up and vice versa.
  - Fifth phase: delegates votes are locked.
  - Sixth phase: the result is calculated. 

Poll creator:
  - Can create but not edit or delete a poll.

Poll creator:
  - Can create but not edit or delete a proposal.

Result:
  - The winners are the proposals with the highest average score.
  - There is one or more winners.
  - If there has been a previous vote with a tie a random proposal wins with equal probability, otherwise the poll goes back to the third period with only the winning proposals.

Prediction evaluation:
  - Prediction scores are updated when the prediction specified time is reached.
  - The voters can vote yes or no (approval voting) if it occurred or not after the time and change their votes dynamically without an end time. The majority decided which alternative wins, which is the evaluation of the prediction.
  - It is always updated in such a way that no predictor can choose not to make certain prediction bets and gain a higher or keep the same prediction score as a result from it. This means that a predictor making any prediction bet on one proposal on a poll (if it was in general they would never be able to take a break) will have to make prediction bets for all of them or otherwise lose points from their prediction score. 
  - To make sure predictors do not need to make prediction bets on predictions that are clearly one way or the other, they can make them on predictions where there have been prediction bets that 1) differ (otherwise they can gain score by predicting things that everyone agrees upon) and 2) have a number of predictors with high enough prediction scores that have previously made prediction bets on the given prediction. 
  - Predictions are ordered by the sum of the predictors prediction scores that bet on it, the more the higher up, and higher if there has been a counter bet.

Prediction evaluation problems: 
  - The colluding predictor problem: what if some subset of predictors bet in a way such that they are differing and with high enough prediction scores during "the last second" so that others are lowered relative to theirs? 
  - The colluding predictor problem is improbable to create an asymmetry this way with a large set (more improbable the more members), correct bets give more positive and incorrect bets give more negative to the prediction scores so that this is normalized over time if it does happen, and finally a predictor can take such possibilities into account and can fully block such happenings by betting on everything. 
  - The irrelevant prediction problem: what if some subset of predictors add predictions that are irrelevant to the poll or the subject area?

Subject area division:
  - Division of subject areas can be done by a hyper subject area that works to optimize the division of the other subjects continuously.
  - The subject area tree, where more specialization is deeper down the tree, is therefore pruned or added to in order to find subject areas with stable prediction scores.
  - Stable prediction scores require the extraction of stable patterns before the event in the subject area. 

Shared roles
  - Everyone in the group considered is a poll creator, proposal creator, and predictor.

Delegates track record:
  - The history of delegates can be viewed and be commented on by anyone.

Poll quorum:
  - A percentage for how many votes need to be cast can be set as a percentage or number.

How can we ensure strategic voting not creating too large negative effects:
  - This is an empirical question which needs to be tested, even when the assumptions for when this works the best fail to be true to a larger degree, the real world outcomes might not become too negative more often or to such a degree that it is worse than the current system.
  - It is possible to vote on goals as well, but it does not ensure that participants will not try to strategy vote if their goal is not chosen.

*The properties of predictive liquid democracy*

A Condorcet jury is a jury where the following is the case:
  - A majority rule decision by the jury has a probability of over 0.5 to pick a proposal in the set of optimal proposals (regarding a given goal).
  - The members of the jury are independent (in the sense of their probabilities of picking the proposal above being independent).

Properties of a Condorcet jury:
  - According to Condorcet’s jury theorem, as the size of the jury grows, the probability that an optimal proposal is chosen converges to 1 [2]. 
  - There can be Condorcet juries in various subject areas that can be delegated to. 

Optimal sets: 
  - The optimal predictor set (in a subject area) is the set of predictors with the highest prediction score, which needs to be over 0.5. 
  - The optimal proposal set is the set of proposals predicted to be optimal by a predictor in the optimal predictor set with regard to the given goal. 
  - The optimal delegate set is the set of delegates voting on the optimal proposal set. 

Properties of optimal delegates:
  - It is trivially optimal, based on the information internal to the forum, to delegate to an optimal delegate with regard to a given goal. 
  - The set of independent optimal delegates make up a Condorcet jury. 
  - Delegates track record can be checked by the members to check the alignment between the values they claim they have and how they vote given the predictions. This is the way to ensure goal-alignment to some degree. 

A perfect delegate case:
  - A shared goal between all voters, predictors, and delegates.
  - Every voter delegates to a delegate to an independent delegate in the optimal delegate set. 
  - Delegates are rational based on their information. 
  - Delegates know other delegates are rational based on their information, and know about predictive liquid democracy and its properties as outlined. 

Properties of score voting: 
  - Allows for scores to correspond to probabilities, which can create a shared understanding of what the scores mean. 
  - Given a perfect delegate case, delegates will vote honestly with score voting, and the average of the scores for every proposal will be the best estimator for the proposal being optimal.
  - The no favorite betrayal criterion is satisfied meaning that the perceived best set of proposals are always scored to the highest by a rational voter. The perceived worst set of proposals are always scored lowest by a rational voter. Strategic voting may occur among the middle proposals when there is not a shared goal.  

Considering strategic voting using score voting: 
  - It has been shown that the strong Nash equilibrium is the Condorcet winner if voters vote strategically and have full information about what the other voters are going to vote for [3].
  - It is possible to have a prediction market about the strategic voting that is stable to some degree. 
  - Allowing voters to score delegates if there is not a shared goal is not good, because such scoring could easily be strategic.


Optimization outside of predictive liquid democracy:
  - Honesty can possibly be optimized toward outside the scope of predictive liquid democracy.
  - A recommendation mechanism for delegates can be implemented that recommends delegates based on value-alignment by some non-voting based measurement of that (as voting against a delegate with a certain value will happen otherwise), and perhaps also by prediction scores (a delegate with a higher such score is recommended higher than one with a lower even if the value-alignment is perfect). 

Measuring the outcomes:
  - How can we measure how good the system does? By the utility of the members over time perhaps, but how? Can we measure the degree of honesty?

[1]: Hagberg, L. (2023). Collected papers on finitist mathematics and phenomenalism: a digital phenomenology. BoD-Books on Demand.

[2]: De Condorcet, N. (2014). Essai sur l'application de l'analyse à la probabilité des décisions rendues à la pluralité des voix. Cambridge University Press.

[3]: Laslier, J. F. (2006). Strategic approval voting in a large electorate.
