from typing import Tuple

def banner_wrap_str(heading:str,level:int=0)->str:
    '''
    Returns the input string wrapped with a banner with level-0 or level-1
    with level-0 being the biggest banner 
    '''
    ostr = ''
    if level < 1:
        ostr += '='*80 + '\n'
        ostr += '=' + ' '*get_banner_margins(80,len(heading))[0]
        ostr += heading + ' '*get_banner_margins(80,len(heading))[1] + '=\n'
        ostr += '='*80 + '\n'
    else:
        ostr += ' '*20 + '='*40 + '\n'
        ostr += ' '*20 + '=' + ' '*get_banner_margins(40,len(heading))[0]
        ostr += heading + ' '*get_banner_margins(40,len(heading))[1] + '=\n'
        ostr += ' '*20 + '='*40 + '\n'
    return ostr

def get_banner_margins(banner_len:int,heading_len:int)->Tuple[int,int]:
    '''
    Given a heading, returns the left and right margin white-space amounts for
    a banner of length banner_len. Returns a tuple of ints (left-gap,right-gap)
    Assumes that the left and right extremes of the heading part of the banner
    consume one character each. If the heading_len cannot fit into the banner_len
    (0,0) is returned
    '''
    total_ws = banner_len - heading_len - 2
    right_ws = max(0,int(total_ws/2))
    left_ws  = max(0,total_ws - right_ws)
    return left_ws,right_ws