# Copyright 2022 Sebastian Ahmed
# This file, and derivatives thereof are licensed under the Apache License, Version 2.0 (the "License");
# Use of this file means you agree to the terms and conditions of the license and are in full compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESSED OR IMPLIED.
# See the License for the specific language governing permissions and limitations under the License.

from prettytable import PrettyTable

class PrettierTable(PrettyTable):
    '''
    Extension of PrettyTable which adds a better HTML output specifically
    for the stock_tools application by overriding get_html_string()
    '''

    def get_html_string(self)->str:
        '''
        Override with better formatting
        '''
        ostr = '<style>table, th, td {border: 1px solid;}</style>\n'
        ostr += '<table>\n'
        ostr += '  <thead>\n'
        ostr += '    <tr>\n'
        for th in self.field_names:
            ostr += '      <th>' + str(th) + '</th>\n'
        ostr += '    </tr>\n'
        ostr += '  </thead>\n'
        ostr += '  <tbody>\n'
        for tr in self.rows:
            ostr += '    <tr>\n'
            td_idx = 0
            for td in tr:
                td_mod = str(td) # default td entry
                if self.field_names[td_idx] in ['gain','gain_per_share'] and td < 0:
                    td_mod = '<font color="#ff0000">'+str(td)+'</font>'
                elif self.field_names[td_idx] == 'wash' and td==True:
                    td_mod = '<font color="#ffa500">'+str(td)+'</font>'
                elif self.field_names[td_idx] == 'allowed_loss' and td<0:
                    td_mod = '<font color="#ffa500">'+str(td)+'</font>'
                ostr += f'      <td>' + td_mod + '</td>\n'
                td_idx += 1
        ostr += '    </tr>\n'
        ostr += '  </tbody>\n'
        ostr += '<table>\n'

        return ostr

        
