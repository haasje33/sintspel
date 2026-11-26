"""Run: python -m unittest tests.test_show_v2 or python tests/test_show_v2.py."""
import sys
import unittest
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import show_v2 as game


def fixture():
    s={'players':[{'id':'p'+str(i),'name':'P'+str(i),'token':'t'+str(i)} for i in range(1,5)],
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
        if self.s['show2']['mode']=='gift':self.a('v2_gift_done')

    def test_phone_spin_rotates_and_host_is_fallback(self):
        self.assertEqual(game.view(self.s,pid='p1')['spin_player'],'p1')
        with self.assertRaises(ValueError):self.p('p2','v2_spin')
        self.p('p1','v2_spin')
        self.assertEqual(self.s['show2']['mode'],'spinning')
        self.assertEqual(game.view(self.s,pid='p1')['spin_player'],'p2')
        game.admin(self.s,{'action':'v2_open_game'},self.save)
        self.a('v2_return_wheel')
        self.assertEqual(self.s['show2']['mode'],'wheel')
        self.assertEqual(game.view(self.s,pid='p1')['spin_player'],'p1')
        self.a('v2_spin')  # Host spins on behalf of the missing phone.
        self.assertEqual(game.view(self.s,pid='p2')['spin_player'],'p2')
        self.a('v2_open_game')
        game.gift_start(self.s,['p1'],'dice')
        self.a('v2_return_wheel')
        self.assertEqual(game.view(self.s,pid='p1')['spin_player'],'p2')

    def test_escape_from_gift_choice_returns_to_wheel(self):
        self.start('dice')
        game.gift_start(self.s,['p1','p2'],'dice')
        self.assertEqual(self.s['show2']['mode'],'gift')
        self.a('v2_return_wheel')
        self.assertEqual(self.s['show2']['mode'],'wheel')
        self.assertEqual(self.s['show2']['regular_completed'],1)
        self.a('v2_return_wheel')  # Wheel escape is harmless if clicked twice.
        self.assertEqual(self.s['show2']['regular_completed'],1)

    def test_escape_during_grocery_study_and_recall(self):
        sh=self.s['show2']
        sh['mode']='grocery_study';sh['grocery']['phase']='study'
        sh['grocery']['items']=['brood'];sh['grocery']['deadline']=9999999
        self.a('v2_return_wheel')
        self.assertEqual(sh['mode'],'wheel')
        self.assertEqual(sh['grocery']['phase'],'complete')
        self.assertEqual(sh['grocery']['items'],[])
        sh['mode']='grocery_recall';sh['grocery']['phase']='recall'
        self.a('v2_return_wheel')
        self.assertEqual(sh['mode'],'wheel')
        self.assertEqual(sh['grocery']['phase'],'complete')
        self.assertIsNone(sh['grocery']['deadline'])

    def test_disable_buggy_game_removes_it_for_the_evening(self):
        self.a('v2_spin')
        bad=self.s['show2']['game']['category']
        self.a('v2_open_game')
        self.a('v2_disable_game')
        sh=self.s['show2']
        self.assertEqual(sh['mode'],'wheel')
        self.assertIn(bad,sh['disabled_games'])
        self.assertNotIn(bad,sh['bag'])
        self.assertNotIn(bad,game.view(self.s)['enabled_games'])
        for _ in range(3):
            if sh['mode']=='wheel':self.a('v2_spin')
            self.assertNotEqual(sh['game']['category'],bad)
            self.a('v2_open_game')
            self.a('v2_return_wheel')
        self.assertIn(bad,sh['disabled_games'])
        self.a('v2_enable_game',category=bad)
        self.assertNotIn(bad,sh['disabled_games'])
        self.assertIn(bad,sh['bag'])

    def test_can_disable_all_and_reenable_one(self):
        for item in game.GAMES:self.a('v2_disable_game',category=item['id'])
        self.assertEqual(game.view(self.s)['enabled_games'],[])
        with self.assertRaisesRegex(ValueError,'uitgeschakeld'):self.a('v2_spin')
        self.a('v2_enable_game',category='dice')
        self.a('v2_spin')
        self.assertEqual(self.s['show2']['game']['category'],'dice')

    def test_disabling_during_gift_choice(self):
        self.start('dice')
        game.gift_start(self.s,['p1','p2'],'dice')
        self.a('v2_disable_game',category='dice')
        self.assertEqual(self.s['show2']['mode'],'wheel')
        self.assertIn('dice',self.s['show2']['disabled_games'])

    def test_host_and_tv_state_renders_at_startup_and_during_show(self):
        """Regression: server must never send show=null (stuck loading screen)."""
        setup=fixture()
        for is_admin in (True,False):
            view=game.view(setup,is_admin=is_admin)
            self.assertIsInstance(view,dict)
            self.assertEqual(view['mode'],'setup')
            self.assertIn('has_story',view)
            self.assertEqual(len(view['games']),8)
            if is_admin:
                self.assertEqual(view['hitster_count'],len(setup['hitster_cards']))
                self.assertEqual(view['hitster_cards'],setup['hitster_cards'])
            else:
                self.assertNotIn('hitster_cards',view)
        self.assertEqual(game.view(self.s)['mode'],'wheel')
        game.admin(self.s,{'action':'v2_direct','category':'dice'},self.save)
        running=game.view(self.s,is_admin=True)
        self.assertEqual(running['mode'],'game')
        self.assertEqual(running['game']['category'],'dice')
        game.admin(self.s,{'action':'v2_return_wheel'},self.save)
        self.assertEqual(game.view(self.s)['mode'],'wheel')
        self.s['show2']['grocery']['phase']='study'
        self.s['show2']['grocery']['items']=['brood','melk']
        self.s['show2']['mode']='grocery_study'
        grocery=game.view(self.s,is_admin=True)
        self.assertEqual(grocery['grocery']['items'],['brood','melk'])
        self.s['show2']['mode']='gift'
        self.s['show2']['gift']={'winners':['p1'],'category':'dice','scores':{'p1':2}}
        gift=game.view(self.s,is_admin=True)
        self.assertEqual(gift['gift']['winners'],['p1'])

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

    def test_packaged_library_excludes_unusable_tracks(self):
        import json
        library=Path(__file__).resolve().parents[1]/'data'/'music-library.json'
        payload=json.loads(library.read_text(encoding='utf-8'))
        self.assertEqual(len(payload['cards']),130)
        excluded=set(payload['excluded_urls'])
        self.assertEqual(len(excluded),2)
        self.assertIn('www.hitstergame.com/nl/00150',excluded)
        self.assertNotIn('www.hitstergame.com/nl/00150',{c['url'] for c in payload['cards']})
        state={'hitster_cards':[{'id':'old','url':'https://www.hitstergame.com/nl/00150',
                                'artist':'Gotye','title':'Somebody That I Used to Know','year':2011}]}
        game.load_packaged_library(state,library)
        self.assertEqual(len(state['hitster_cards']),130)
        self.assertFalse(any(c.get('title')=='Somebody That I Used to Know' for c in state['hitster_cards']))

    def test_additional_music_cards_keep_requested_quiz_years(self):
        import json
        library=Path(__file__).resolve().parents[1]/'data'/'music-library.json'
        payload=json.loads(library.read_text(encoding='utf-8'))
        songs={x['title']:x for x in payload['cards']}
        self.assertEqual(len(songs),130)
        self.assertEqual((songs['Watermelon Sugar']['card_year'],songs['Watermelon Sugar']['year']),(2020,2020))
        self.assertEqual((songs['Bad Habits']['card_year'],songs['Bad Habits']['year']),(2024,2021))
        self.assertEqual(songs['Watermelon Sugar']['url'],'www.hitstergame.com/nl/aaaa0006/00115')
        self.assertEqual(songs['Bad Habits']['url'],'www.hitstergame.com/nl/00282')
        state={'hitster_cards':[]}
        self.assertEqual(game.load_packaged_library(state,library),130)
        self.assertEqual(len(state['hitster_cards']),130)
        self.assertEqual(len({x['url'] for x in state['hitster_cards']}),130)

    def test_solo_testing_can_reveal_with_missing_answers(self):
        # Host can progress without any of the four player phones.
        for category in ('classic','quiz','dice','taboo'):
            self.s['show2']['mode']='wheel'
            g=self.start(category)
            if category=='classic':self.a('v2_choose',value='medium')
            if category=='quiz':self.a('v2_choose',value='80s & 90s')
            self.a('v2_reveal')
            self.assertEqual(g['phase'],'reveal')
            self.assertTrue(all(score==0 for score in g['scores'].values()))
            self.a('v2_next')
            self.assertEqual(g['phase'],'choose' if category in ('classic','quiz') else 'answer')
            self.a('v2_return_wheel')

    def test_quiplash_works_with_zero_or_one_answers_and_no_votes(self):
        g=self.start('quiplash')
        self.p('p1','v2_answer','Mijn grappige antwoord')
        self.a('v2_open_vote')
        self.assertEqual(len(g['rounds'][0]['option_tokens']),1)
        self.a('v2_reveal')
        self.assertTrue(all(score==0 for score in g['scores'].values()))
        self.a('v2_next')
        self.a('v2_open_vote')
        self.assertEqual(len(g['rounds'][1]['option_tokens']),0)
        self.a('v2_reveal')
        self.assertTrue(all(score==0 for score in g['scores'].values()))

    def test_card_duel_zero_and_partial_guesses_do_not_get_free_points(self):
        g=self.start('cards')
        r=g['rounds'][0]
        self.a('v2_reveal')
        self.assertTrue(r['deal_finished'])
        self.assertEqual(r['deal_winners'],[])
        self.assertTrue(all(score==0 for score in g['scores'].values()))
        self.a('v2_next')
        self.assertEqual(g['round_index'],1)
        r=g['rounds'][1]
        wrong='black' if r['cards'][0]['s'] in 'HD' else 'red'
        self.p('p1','v2_answer',wrong)
        self.a('v2_reveal')
        self.assertEqual(r['deal_winners'],[])
        self.assertTrue(all(score==0 for score in g['scores'].values()))

    def test_investigator_and_groceries_can_finish_without_answers(self):
        g=self.start('three')
        self.a('v2_reveal')
        self.assertEqual(g['phase'],'reveal')
        self.assertTrue(all(score==0 for score in g['scores'].values()))
        self.assertTrue(game.view(self.s,is_admin=True)['game']['current']['guess_skipped'])
        self.a('v2_return_wheel')
        sh=self.s['show2'];gr=sh['grocery']
        sh['mode']='grocery_recall';gr['phase']='recall';gr['items']=['brood','melk']
        gr['deadline']=time.time()+180
        self.a('v2_grocery_close')
        self.assertEqual(sh['mode'],'grocery_review')
        self.assertEqual({result['score'] for result in gr['review'].values()},{0})

    def test_wheel_result_is_hidden_until_spin_animation_ends(self):
        root=Path(__file__).resolve().parents[1]
        client=(root/'static'/'v2.js').read_text(encoding='utf-8')
        style=(root/'static'/'v2.css').read_text(encoding='utf-8')
        self.assertIn('wheel-result-pending',client)
        self.assertIn('},6500);}',client)
        self.assertIn('5.05s forwards',style)

    def test_large_screen_layout_is_tv_only(self):
        root=Path(__file__).resolve().parents[1]
        markup=(root/'static'/'index.html').read_text(encoding='utf-8')
        client=(root/'static'/'v2.js').read_text(encoding='utf-8')
        css=(root/'static'/'v2.css').read_text(encoding='utf-8')
        self.assertIn("location.pathname==='/screen'",markup)
        self.assertIn("classList.add('tv-display')",markup)
        self.assertIn("side?'with-sidebar':'full-stage'",client)
        self.assertIn("html.tv-display .layout.full-stage",css)
        self.assertIn("html.tv-display .wheel-wrap",css)
        self.assertIn("html.tv-display .grocery-list",css)
        self.assertIn("html.tv-display .tv-mini-join",css)
        self.assertIn("html.tv-display .player-details strong",css)
        self.assertIn("clamp(64px,3.12vw,118px)",css)

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

    def test_quiplash_tie_gives_each_winner_one_gift(self):
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
        self.assertEqual(sorted(game.view(self.s)['gift']['winners']),['p1','p2'])
        self.complete_gift()
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


class RuleChangeTests(unittest.TestCase):
    """Sintspel 2.1: winners pick a gift, randomised Wie van de 3?, Pepernotenpong."""
    def setUp(self):
        self.s=fixture()
        self.save=lambda:None
        game.admin(self.s,{'action':'v2_start'},self.save)
    def a(self,action,**kwargs):
        return game.admin(self.s,{'action':action,**kwargs},self.save)
    def p(self,pid,action,value=None):
        return game.submit(self.s,{'action':action,'value':value},pid,self.save)
    def to_review(self,category,points):
        self.a('v2_direct',category=category)
        g=self.s['show2']['game']
        g['phase']='review'
        g['scores']=dict(points)
        return g
    def give_all(self):
        if self.s['show2']['mode']=='gift':self.a('v2_gift_done')

    def test_zero_points_means_no_winner_and_no_gift(self):
        self.to_review('dice',{'p1':0,'p2':0,'p3':0,'p4':0})
        self.assertEqual(self.a('v2_confirm')['winners'],[])
        self.assertIn(self.s['show2']['mode'],('wheel','grocery_alarm'))  # alarm may follow game 1
        self.assertEqual(self.s['show2']['regular_completed'],1)

    def test_three_tied_top_scorers_each_take_one_gift(self):
        self.to_review('dice',{'p1':3,'p2':3,'p3':3,'p4':2})
        self.assertEqual(self.a('v2_confirm')['winners'],['p1','p2','p3'])
        self.assertEqual(self.s['show2']['mode'],'gift')
        self.assertEqual(game.view(self.s)['gift']['winners'],['p1','p2','p3'])
        self.a('v2_gift_done')
        self.assertIn(self.s['show2']['mode'],('wheel','grocery_alarm'))
        self.assertEqual(self.s['show2']['regular_completed'],1)

    def test_host_ends_evening_after_grocery_recall(self):
        gr=self.s['show2']['grocery']
        gr.update(phase='waiting',items=game.GROCERIES[:20],recall_after=99)
        self.a('v2_finish')
        self.assertEqual(self.s['show2']['mode'],'grocery_alarm')
        self.assertEqual(gr['phase'],'alarm_recall')
        self.a('v2_grocery_show')
        self.p('p2','v2_grocery_answer','\n'.join(gr['items'][:5]))
        self.a('v2_grocery_close')
        self.a('v2_grocery_confirm')
        self.assertEqual(game.view(self.s)['gift']['winners'],['p2'])
        self.a('v2_gift_done')
        self.assertEqual(self.s['show2']['mode'],'finished')
        self.a('v2_resume')
        self.assertEqual(self.s['show2']['mode'],'wheel')

    def test_host_ends_evening_directly_without_pending_recall(self):
        self.a('v2_finish')
        self.assertEqual(self.s['show2']['mode'],'finished')
        with self.assertRaises(ValueError):self.a('v2_finish')

    def test_three_owners_are_a_random_derangement(self):
        seen=set()
        for _ in range(60):
            pairs=game.random_pairs(['p1','p2','p3','p4'])
            self.assertEqual(sorted(i for i,_ in pairs),['p1','p2','p3','p4'])
            self.assertEqual(sorted(o for _,o in pairs),['p1','p2','p3','p4'])
            self.assertTrue(all(i!=o for i,o in pairs))
            seen.add(tuple(map(tuple,pairs)))
        self.assertGreater(len(seen),10)
        # Not always "the next seat" anymore.
        nxt={'p1':'p2','p2':'p3','p3':'p4','p4':'p1'}
        self.assertTrue(any(any(nxt[i]!=o for i,o in p) for p in seen))

    def test_three_needs_new_stories_after_it_was_played(self):
        g=self.to_review('three',{'p1':3,'p2':0,'p3':0,'p4':0})
        old=self.s['show2']['stories']['p1']
        self.a('v2_confirm')
        self.give_all()
        self.assertEqual(self.s['show2']['stories'],{})
        view=game.view(self.s)
        self.assertTrue(view['stories_needed'])
        with self.assertRaises(ValueError):self.p('p1','v2_story',old)  # reused story
        self.s['show2']['mode']='wheel'
        self.s['show2']['bag']=['three']
        with self.assertRaises(ValueError):self.a('v2_spin')
        with self.assertRaises(ValueError):self.a('v2_direct',category='three')
        self.s['show2']['bag']=['three','dice']
        for _ in range(10):
            self.a('v2_spin');self.assertEqual(self.s['show2']['game']['category'],'dice')
            self.a('v2_return_wheel')
        for i,p in enumerate(self.s['players']):self.p(p['id'],'v2_story','Een gloednieuw waar verhaal nummer %d'%i)
        self.a('v2_direct',category='three')
        self.assertEqual(self.s['show2']['game']['category'],'three')

    def test_pepernotenpong_is_an_intermezzo_without_bag_gifts(self):
        self.a('v2_direct',category='pong')
        g=self.s['show2']['game']
        self.assertEqual(g['phase'],'play')
        order=g['rounds'][0]['order']
        self.assertEqual(sorted(order),['p1','p2','p3','p4'])
        view=game.view(self.s)
        self.assertEqual(view['game']['current']['order'],order)
        self.assertEqual(view['game']['current']['throws'],game.PONG_THROWS)
        self.a('v2_pong_finish')
        self.assertEqual(self.s['show2']['mode'],'wheel')
        self.assertNotIn('pong',self.s['show2']['bag'])
        self.assertEqual(self.s['show2']['regular_completed'],0)

    def test_classic_hard_is_tight(self):
        for _ in range(40):
            r=game.find_classic(self.s,'hard')
            self.assertIsNotNone(r)
            years=[r['year']]+[c['year'] for c in r['ref']]
            close=min(abs(r['year']-c['year']) for c in r['ref'])
            self.assertTrue(1<=close<=3 and max(years)-min(years)<=12,years)
            r=game.find_classic(self.s,'medium')
            close=min(abs(r['year']-c['year']) for c in r['ref'])
            self.assertTrue(4<=close<=8,r)

    def test_grocery_singular_and_plural_match(self):
        for guess,item in [('appel','appels'),('banaan','bananen'),('tomaat','tomaten'),('ei','eieren'),
                           ('druif','druiven'),('kip filet','kipfilet')]:
            self.assertTrue(game.same_grocery(guess,item),(guess,item))
        for guess,item in [('zout','zalm'),('melk','mais'),('pasta','paprika')]:
            self.assertFalse(game.same_grocery(guess,item),(guess,item))

    def test_configure_rejects_without_partial_changes(self):
        fresh=fixture()
        before=[p['name'] for p in fresh['players']]
        with self.assertRaises(ValueError):
            game.admin(fresh,{'action':'v2_configure','players':[{'name':'Jan'}]*4},self.save)
        self.assertEqual([p['name'] for p in fresh['players']],before)

    def test_reset_frees_seats_and_clears_stories(self):
        self.a('v2_reset',confirmation='RESET')
        self.assertTrue(all(p['token'] is None for p in self.s['players']))
        self.assertEqual(self.s['show2']['stories'],{})

    def test_release_seat(self):
        self.a('v2_release_seat',player='p2')
        self.assertIsNone(self.s['players'][1]['token'])
        self.assertEqual(self.s['players'][0]['token'],'t1')

    def test_tv_sees_grocery_scores_and_taboo_attempts(self):
        self.a('v2_direct',category='taboo')
        r=self.s['show2']['game']['rounds'][0]
        self.p(r['performer'],'v2_start_timer')
        guesser=next(p for p in game.player_ids(self.s) if p!=r['performer'])
        self.p(guesser,'v2_guess','iets')
        tv=game.view(self.s)
        self.assertEqual(tv['game']['current']['attempt_count'],1)
        self.assertNotIn('word',tv['game']['current'])

if __name__=='__main__':unittest.main()