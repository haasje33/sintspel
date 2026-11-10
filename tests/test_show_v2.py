"""Run: python -m unittest tests.test_show_v2 or python tests/test_show_v2.py."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import show_v2 as game


def fixture():
    s={'players':[{'id':'p'+str(i),'name':'P'+str(i),'target':9,'received':0,'wins':0,'token':'t'+str(i)} for i in range(1,5)],
       'hitster_cards':[{'id':str(i),'artist':'The Band '+str(i),
                         'title':'Track '+str(i),'year':1960+(i%67),'url':'https://example.test/'+str(i)} for i in range(140)],
       'history':[],'show2':game.new_show()}
    for p in s['players']:s['show2']['stories'][p['id']]='Ik heb ooit iets geks gedaan in mijn jeugd '+p['id']
    return s


class ShowTests(unittest.TestCase):
    def setUp(self):
        self.s=fixture()
        self.log=[]
        self.save=lambda:self.log.append(1)
        game.admin(self.s,{'action':'v2_start'},self.save)

    def a(self,action,**kwargs):
        return game.admin(self.s,{'action':action,**kwargs},self.save)
    def p(self,pid,action,value=None):
        return game.submit(self.s,{'action':action,'value':value},pid,self.save)
    def start(self,category):
        self.a('v2_direct',category=category)
        return self.s['show2']['game']
    def complete_gift(self):
        while self.s['show2']['mode']=='gift':
            need=game.gift_requirement(self.s)
            if need is None:break
            self.a('v2_give',recipient=need['eligible'][0])

    def test_fuzzy_examples(self):
        for a,b,k in [('queen','Queen','artist'),('Police','The Police','artist'),
                      ('Simon en Garfunkel','Simon & Garfunkel','artist'),
                      ('Lady Gaga','Lady Gaga & Bradley Cooper','artist'),
                      ('Johnny Be Good','Johnny B. Goode','title'),
                      ('Simply The Best','The Best','title'),
                      ('Celine Dion','Céline Dion','artist')]:
            self.assertTrue(game.same_answer(a,b,k),f'{a} != {b}')
        self.assertFalse(game.same_answer('Love','Love Me Do','title'))
        self.assertFalse(game.same_answer('Hello','Hello Goodbye','title'))

    def test_packaged_music_library_and_old_cards(self):
        import json
        import tempfile
        demo={'cards':[{'url':'www.example.org/music/001','artist':'Correct Artist',
                       'title':'Right Track','card_year':1980,'year':1990}],
              'excluded_urls':['www.example.org/music/002']}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'library.json'
            path.write_text(json.dumps(demo),encoding='utf-8')
            state={'hitster_cards':[
                {'id':'old','url':'https://www.example.org/music/001','artist':'Old','title':'Old','year':1980},
                {'id':'wrong','url':'www.example.org/music/002','artist':'Wrong','title':'Bad','year':1980}]}
            self.assertEqual(game.load_packaged_library(state,path),0)
            self.assertEqual(len(state['hitster_cards']),1)
            self.assertEqual(state['hitster_cards'][0]['year'],1990)
            self.assertEqual(state['hitster_cards'][0]['url'],'www.example.org/music/001')
            self.assertEqual(state['hitster_cards'][0]['id'],'old')

    def test_dice_yahtzee_separate(self):
        g=self.start('dice');r=g['rounds'][0]
        r['rule']='target';r['target']=6
        for pid,values in [('p1',[3]*5),('p2',[6,6,6,6,2]),('p3',[6,6,3,4,2]),('p4',[1,2,3,4,5])]:
            self.p(pid,'v2_answer',values)
        self.a('v2_reveal')
        self.assertEqual(g['scores']['p1'],3)
        self.assertEqual(g['scores']['p2'],1)
        self.assertEqual(g['scores']['p3'],0)
        self.assertEqual(g['scores']['p4'],0)

    def test_quiz_and_manual_override(self):
        g=self.start('quiz')
        self.p('p2','v2_choose','80s & 90s') if g['rounds'][0]['chooser']=='p2' else self.a('v2_choose',value='80s & 90s')
        r=g['rounds'][0]
        self.assertIn('hidden_id',r)
        for pid in game.player_ids(self.s):
            val='nonsense'
            if r['question_type'] in ('artist','title'):val='wrong answer'
            elif r['question_type'] in ('year3','year5'):val=1950
            else:val='before' if r['year']>=r['boundary'] else 'after'
            self.p(pid,'v2_answer',val)
        self.a('v2_reveal')
        self.assertFalse(r['grades']['p1']['accepted'])
        self.a('v2_override',round=0,player='p1',accepted=True)
        self.assertEqual(g['scores']['p1'],1)
        self.a('v2_override',round=0,player='p1',accepted=False)
        self.assertEqual(g['scores']['p1'],0)

    def test_classic_card_generation(self):
        g=self.start('classic')
        for level in ('easy','medium','hard'):
            c=game.find_classic(self.s,level)
            self.assertIsNotNone(c,level)
            years=[c['ref'][0]['year'],c['year'],c['ref'][1]['year']]
            self.assertEqual(len(set(years)),3)
        self.a('v2_choose',value='medium')
        r=g['rounds'][0]
        self.assertIn(r['correct'],('left','middle','right'))
        self.assertNotIn('song',game.view(self.s)['game']['current'])

    def test_quiplash_tie_and_two_gifts(self):
        g=self.start('quiplash')
        for i in range(4):
            r=g['rounds'][i]
            for pid in game.player_ids(self.s):self.p(pid,'v2_answer','fun '+pid)
            self.a('v2_open_vote')
            for pid,target in [('p1','p2'),('p2','p1'),('p3','p2'),('p4','p1')]:
                option=next(tok for tok,owner in r['option_tokens'].items() if owner==target)
                self.p(pid,'v2_vote',option)
            self.a('v2_reveal')
            self.assertEqual(g['rounds'][i]['points']['p1'],1)
            self.assertEqual(g['rounds'][i]['points']['p2'],1)
            self.a('v2_next')
        self.assertEqual(g['phase'],'review')
        self.a('v2_confirm')
        need=game.gift_requirement(self.s)
        self.assertEqual(len(self.s['show2']['gift']['winners']),2)
        self.assertEqual(need['kind'],'self')
        self.complete_gift()
        self.assertEqual(sum(p['received'] for p in self.s['players']),4)
        self.assertEqual(self.s['show2']['regular_completed'],1)

    def test_cards_eliminations(self):
        g=self.start('cards');r=g['rounds'][0]
        for pid in game.player_ids(self.s):self.p(pid,'v2_answer','red')
        self.a('v2_reveal')
        if r.get('deal_winners'):
            self.assertEqual(g['phase'],'reveal')
        else:
            self.a('v2_next')
            self.assertEqual(g['phase'],'answer')
            self.assertEqual(r['stage'],1)

    def test_secret_story_until_end(self):
        g=self.start('three')
        self.assertNotIn('owner',game.view(self.s)['game']['current'])
        for i in range(4):
            r=g['rounds'][i]
            guess=next(p for p in game.player_ids(self.s) if p!=r['investigator'])
            self.p(r['investigator'],'v2_guess_owner',guess)
            self.assertEqual(g['phase'],'reveal')
            self.a('v2_next')
        self.assertEqual(g['phase'],'review')

    def test_wheel_cycle_grocery_two_alarms(self):
        for i,category in enumerate(['quiplash','dice','cards','three','taboo']):
            self.s['show2']['regular_completed']=i+1
            game.trigger_transition(self.s)
            mode=self.s['show2']['mode'];gr=self.s['show2']['grocery']
            if mode=='grocery_alarm' and gr['phase']=='alarm_intro':
                self.a('v2_grocery_show')
                self.assertEqual(len(gr['items']),20)
                gr['deadline']=1
                self.a('v2_grocery_close')
                self.assertEqual(gr['phase'],'waiting')
            if gr['phase']=='waiting' and self.s['show2']['regular_completed']>=gr['recall_after']:
                game.trigger_transition(self.s)
                self.assertEqual(gr['phase'],'alarm_recall')
                self.a('v2_grocery_show')
                self.assertEqual(gr['phase'],'recall')
                for pid in game.player_ids(self.s):
                    self.p(pid,'v2_grocery_answer','\n'.join(gr['items'][:i+1]))
                self.a('v2_grocery_close')
                self.assertEqual(gr['phase'],'review')
                self.a('v2_grocery_confirm')
                self.complete_gift()
                break


if __name__=='__main__':unittest.main()
