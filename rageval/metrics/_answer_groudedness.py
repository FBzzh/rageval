# -*- coding: utf-8 -*-

import pytest
import numpy as np
import pandas as pd
from abc import ABC
from typing import List, Any


from datasets import Dataset
from dataclasses import dataclass

from rageval.metrics import Metric
from rageval.models import NLIModel
from rageval.utils import text_to_sents


@dataclass
class AnswerGroundedness(Metric):
    """
    Estimates answer groundedness by estimating citation precision/recall using answer and retrieved context.

    Attributes
    ----------
    name : str
    batch_size : int, Batch size for openai completion.

    """

    name: str = "answer_groundednss"  # type: ignore
    batch_size: int = 2

    def init_model(self, task: str = "sentiment-analysis", model: str = "roberta-large-mnli"):
        """Initializee the LLM model with OpenAILLM."""
        self.model: NLIModel = NLIModel(task, model)

    def _verify_by_stance(self, claim: str, evidences: List[str]) -> Any:
        """Verify the faithfulness of the `claim` based on `evidences`."""
        labels = []
        for evidence in evidences:
            label = self.model.infer(premise=evidence, hypothesis=claim)
            labels.append(label)
        if "support" in labels:
            return True
        elif "refute" in labels:
            return False
        else:
            return False

    def _score(
        self,
        answer: str,
        evidences: List[str],
    ) -> list:
        """
        Evaluate the groundedness of an answer.

        Firstly,split the answer into a set of claims.
        Then, compute the faithfulness score of each claim. The faithfulness is a binary score.
        Finally, aggregate all faithfulness score of each claim.
        """

        results = []
        # decompose answers into a list of claim
        claims = text_to_sents(answer)

        for i, claim in enumerate(claims):
            # obtain the faithfulness of each claim by language inference model.
            label = self._verify_by_stance(claim, evidences)
            results.append({
                "claim": claim,
                "evidence": evidences[i],
                "reasoning": "",
                "error": "",
                "factuality": label,
            })
        df = pd.DataFrame(results)
        return all(df['factuality']), df

    def _score_batch(
        self,
        dataset: Dataset,
        callback_group_name: str = "batch",
    ) -> list:
        """
        Evaluate the groundedness of a batch of answers.

        Firstly,split the answer into a set of claims.
        Then, compute the faithfulness score of each claim. The faithfulness is a binary score.
        Finally, aggregate all faithfulness score of each claim.
        """

        answers, contexts = (
            dataset["answers"],
            dataset["contexts"],
        )

        results = []
        for i, answer in enumerate(answers):
            # decompose answers into a list of claim
            _, r = self._score(answer, contexts[i])

            results.append(r)
        df = pd.concat(results)
        return all(df['factuality']), df