import pandas as pd

from zipline.pipeline import Pipeline
from zipline.pipeline.data.testing import TestingDataSet
from zipline.pipeline.domain import USEquities
from zipline.pipeline.factors import CustomFactor
import zipline.testing.fixtures as zf
from zipline.testing.core import powerset
from zipline.testing.predicates import assert_equal


class Sum(CustomFactor):

    def compute(self, today, assets, out, data):
        out[:] = data.sum(axis=0)

    @classmethod
    def create(cls, column, window_length):
        return cls(inputs=[column], window_length=window_length)


class MixedGenericsTestCase(zf.WithSeededRandomPipelineEngine,
                            zf.ZiplineTestCase):
    START_DATE = pd.Timestamp('2014-01-02', tz='utc')
    END_DATE = pd.Timestamp('2014-01-31', tz='utc')
    ASSET_FINDER_EQUITY_SIDS = (1, 2, 3, 4, 5)
    ASSET_FINDER_COUNTRY_CODE = 'US'

    def create_equivalent_sums(self, length):
        dataset = TestingDataSet
        return [
            Sum.create(dataset.float_col, length),
            Sum.create(dataset.float_col.specialize(USEquities), length),
            Sum.create(dataset.specialize(USEquities).float_col, 1),
        ]

    def test_mixed_generics(self):
        """
        Test that we can run pipelines with mixed generic/non-generic terms.

        This test is a regression test for failures encountered during
        development where having a mix of generic and non-generic columns in
        the term graph caused bugs in our extra row accounting.
        """
        USTestingDataSet = TestingDataSet.specialize(USEquities)
        base_terms = {
            'sum3_generic': Sum.create(TestingDataSet.float_col, 3),
            'sum3_special': Sum.create(USTestingDataSet.float_col, 3),
            'sum10_generic': Sum.create(TestingDataSet.float_col, 10),
            'sum10_special': Sum.create(USTestingDataSet.float_col, 10),
        }

        def run(ts):
            pipe = Pipeline(ts, domain=USEquities)
            start = self.trading_days[-5]
            end = self.trading_days[-1]
            return self.run_pipeline(pipe, start, end)

        base_result = run(base_terms)

        for subset in powerset(base_terms):
            subset_terms = {t: base_terms[t] for t in subset}
            result = run(subset_terms).sort_index(axis=1)
            expected = base_result[list(subset)].sort_index(axis=1)
            assert_equal(result, expected)