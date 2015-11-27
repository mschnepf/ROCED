# ===============================================================================
#
# Copyright (c) 2010, 2011 by Thomas Hauth and Stephan Riedel
# 
# This file is part of ROCED.
# 
# ROCED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# ROCED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with ROCED.  If not, see <http://www.gnu.org/licenses/>.
#
# ===============================================================================


import logging

from Core import ScaleTest
from RequirementAdapter import Requirement


class RequirementBoxTest(ScaleTest.ScaleTestBase):
    def test_getReq(self):
        box = Requirement.RequirementBox()

        box.adapterList.append(Requirement.RequirementAdapterBase("type1"))

        box.adapterList.append(Requirement.RequirementAdapterBase("type2"))
        box.adapterList.append(Requirement.RequirementAdapterBase("type3"))
        box.adapterList.append(Requirement.RequirementAdapterBase("type2"))

        self.assertEqual(len(box.getMachineTypeRequirement()), 3)
        self.assertEqual(box.getMachineTypeRequirement()["type2"], 0)
        logging.debug(str(box.getMachineTypeRequirement()))

        box.adapterList[1]._curRequirement = 3
        box.adapterList[3]._curRequirement = 2

        self.assertEqual(len(box.getMachineTypeRequirement()), 3)
        self.assertEqual(box.getMachineTypeRequirement()["type2"], 5)
        logging.debug(str(box.getMachineTypeRequirement()))