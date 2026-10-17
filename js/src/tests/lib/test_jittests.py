# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
from types import SimpleNamespace

from .jittests import JitTest, OutputStatus, check_output


class ExpectedErrorStatusTests(unittest.TestCase):
    def test_wrong_exception_is_a_failure_status(self):
        test = JitTest("expected-error.js")
        test.expect_error = "ReferenceError"
        status = check_output(
            "", "TypeError: wrong exception", 3, False, test, SimpleNamespace()
        )
        self.assertIs(status, OutputStatus.FAILED)

    def test_matching_exception_is_an_ok_status(self):
        test = JitTest("expected-error.js")
        test.expect_error = "ReferenceError"
        status = check_output(
            "", "ReferenceError: expected exception", 3, False, test, SimpleNamespace()
        )
        self.assertIs(status, OutputStatus.OK)


if __name__ == "__main__":
    unittest.main()
