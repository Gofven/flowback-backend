## Flowback Backend
Flowback was created and project lead by Loke Hagberg. The co-creators of this version were:
Siamand Shahkaram, Emil Svenberg and Yuliya Hagberg.
It is a decision making platform.

<sub><sub>This text is not allowed to be removed.</sub></sub>

\documentclass{article}

\usepackage{url, hyperref, amssymb, amsmath}
\thispagestyle{empty}


\begin{document}

The following is from Collected papers on finitist mathematics and phenomenalism: a digital phenomenology by Loke Hagberg 2023 \cite{predictiveliquiddemocracy}.

\section*{Predictive liquid democracy}


The following outlines predictive liquid democracy. Combining prediction markets and liquid democracy into predictive liquid democracy was done theoretically (see 'föreningen för Digital demokrati' in Sweden) independently by me ('independently' if someone else may have stated its properties) when the Flowback project was in an early stage (2021). This decision system is anti-fragile, as it learns from any mistake if the mechanisms work well enough.

*Predictive liquid democracy as implemented in Flowback 2023-01*

Voter:
\begin{itemize}
  \item Can vote (with equal weight).
  \item Have secret votes.
  \item Can delegate temporally in any subject area as long as they want.
  \item Can override their delegate by voting themselves or changing delegate before a poll deadline.
  \item Can become or stop being a delegate.
\end{itemize}

Delegate:
\begin{itemize}
  \item Can vote (with the weight of delegations to them and possibly their own vote if they are a voter as well).
  \item Have public votes.
  \item Can not delegate (no meta-delegation).
\end{itemize}

Predictor:
\begin{itemize}
  \item Can create predictions (the outcome of one or more relevant variables until a specified time).
  \item Can bet a probability on a prediction.
  \item Have prediction scores (between 0 and 1) based on how well they bet probabilities.
  \item Predictors might be an artificial intelligence, an algorithm, or a human with an internal model for example. 
\end{itemize}

Poll:
\begin{itemize}
  \item Is a question where proposals are potential answers.
  \item Are created by a poll creator.
  \item Has a subject area.
  \item Has phases.
\end{itemize}

Separate poll phases
\begin{itemize}
  \item First phase: proposals can be inputted by proposal creators.
  \item Second phase: proposals can no longer be inputted. Predictions and their probabilities can be inputted by predictors.
  \item Third phase: predictions and their probability bets can no longer be inputted. Voters and delegates can input scores (they can vote). Proposal scores determine their position in the proposal list displayed where higher score means higher up.
  \item Fourth phase: delegates votes are locked. Prediction probability bets cannot be shown before this phase.
  \item Fifth phase: the result is calculated.
\end{itemize}

Poll creator:
\begin{itemize}
  \item Can create but not edit or delete a poll.
\end{itemize}

Poll creator:
\begin{itemize}
  \item Can create but not edit or delete a proposal.
\end{itemize}

Result:
\begin{itemize}
  \item The winners are the proposals with the highest average score.
  \item There is one or more winners.
  \item If there has been a previous vote with a tie a random proposal wins with equal probability, otherwise the poll goes back to the third period with only the winning proposals.
\end{itemize}

Prediction evaluation:
\begin{itemize}
  \item Prediction scores are updated when the prediction specified time is reached.
  \item The voters can vote yes or no if it occurred or not after the time and change their votes dynamically without an end time. The majority decided which alternative wins, which is the evaluation of the prediction.
  \item It is always updated in such a way that no predictor can choose not to make certain predictions and gain a higher or keep the same prediction score as a result from it.
\end{itemize}

Subject area division:
\begin{itemize}
  \item Division of subject areas can be done by a hyper subject area that works to optimize the division of the other subjects continuously.
  \item The subject area tree, where more specialization is deeper down the tree, is therefore pruned or added to in order to find subject areas with stable prediction scores.
  \item Stable prediction scores require the extraction of stable patterns before the event in the subject area. 
\end{itemize}

Shared roles
\begin{itemize}
  \item Everyone in the group considered is a poll creator, proposal creator, and predictor.
\end{itemize}

Delegates track record:
\begin{itemize}
  \item The history of delegates can be viewed and be commented on by anyone.
\end{itemize}

Poll quorum:
\begin{itemize}
  \item A percentage for how many votes need to be cast can be set as a percentage or number.
\end{itemize}

How can we ensure strategic voting not creating too large negative effects:
\begin{itemize}
  \item This is an empirical question which needs to be tested, even when the assumptions for when this works the best fail to be true to a larger degree, the real world outcomes might not become too negative more often or to such a degree that it is worse than the current system.
  \item It is possible to vote on goals as well, but it does not ensure that participants will not try to strategy vote if their goal is not chosen.
\end{itemize}


*The properties of predictive liquid democracy*

A Condorcet jury is a jury where the following is the case:
\begin{itemize}
  \item A majority rule decision by the jury has a probability of over 0.5 to pick a proposal in the set of optimal proposals (regarding a given goal).
  \item The members of the jury are independent (in the sense of their probabilities of picking the proposal above being independent).
\end{itemize}

Properties of a Condorcet jury:
\begin{itemize}
  \item According to Condorcet’s jury theorem, as the size of the jury grows, the probability that an optimal proposal is chosen converges to 1 \cite{DeCondorcetJury}. 
  \item There can be Condorcet juries in various subject areas that can be delegated to. 
\end{itemize}

Optimal sets: 
\begin{itemize}
  \item The optimal predictor set (in a subject area) is the set of predictors with the highest prediction score, which needs to be over 0.5. 
  \item The optimal proposal set is the set of proposals predicted to be optimal by a predictor in the optimal predictor set with regard to the given goal. 
  \item The optimal delegate set is the set of delegates voting on the optimal proposal set. 
\end{itemize}

Properties of optimal delegates:
\begin{itemize}
  \item It is trivially optimal, based on the information internal to the forum, to delegate to an optimal delegate with regard to a given goal. 
  \item The set of independent optimal delegates make up a Condorcet jury. 
  \item Delegates track record can be checked by the members to check the alignment between the values they claim they have and how they vote given the predictions. This is the way to ensure goal-alignment to some degree. 
\end{itemize}

A perfect delegate case:
\begin{itemize}
  \item A shared goal between all voters, predictors, and delegates.
  \item Every voter delegates to a delegate to an independent delegate in the optimal delegate set. 
  \item Delegates are rational based on their information. 
  \item Delegates know other delegates are rational based on their information, and know about predictive liquid democracy and its properties as outlined. 
\end{itemize}

Properties of score voting: 
\begin{itemize}
  \item Allows for scores to correspond to probabilities, which can create a shared understanding of what the scores mean. 
  \item Given a perfect delegate case, delegates will vote honestly with score voting, and the average of the scores for every proposal will be the best estimator for the proposal being optimal.
  \item The no favorite betrayal criterion is satisfied meaning that the perceived best set of proposals are always scored to the highest by a rational voter. The perceived worst set of proposals are always scored lowest by a rational voter. Strategic voting may occur among the middle proposals when there is not a shared goal.  
\end{itemize}

Considering strategic voting using score voting: 
\begin{itemize}
  \item It has been shown that the strong Nash equilibrium is the Condorcet winner if voters vote strategically and have full information about what the other voters are going to vote for \cite{strongNashEquilibriumScoreVotingFullInformation}.
  \item It is possible to have a prediction market about the strategic voting that is stable to some degree. 
  \item Allowing voters to score delegates if there is not a shared goal is not good, because such scoring could easily be strategic.
\end{itemize}


\bibliographystyle{unsrt}  
\begin{thebibliography}{}

\bibitem{predictiveliquiddemocracy}
Hagberg, L. (2023). Collected papers on finitist mathematics and phenomenalism: a digital phenomenology. BoD-Books on Demand.

\bibitem{DeCondorcetJury}
De Condorcet, N. (2014). Essai sur l'application de l'analyse à la probabilité des décisions rendues à la pluralité des voix. Cambridge University Press.

\bibitem{strongNashEquilibriumScoreVotingFullInformation}
Laslier, J. F. (2006). Strategic approval voting in a large electorate.

\end{thebibliography}






\end{document}
