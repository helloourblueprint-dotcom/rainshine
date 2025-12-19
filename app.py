import streamlit as st
import random
import copy
from dataclasses import dataclass
from typing import Optional, List

# --- 1. DATA STRUCTURES ---

@dataclass
class RainCard:
    title: str
    weight: int
    exhaust: int
    is_joint: bool = False
    flavor_text: str = ""
    scenario: str = "" # Holds the open-ended connection question
    age: int = 0
    accumulated_tokens: int = 0
    type: str = "Rain" 
    discussed: bool = False

    def exhaust_value(self):
        return self.exhaust + self.accumulated_tokens

@dataclass
class Player:
    name: str
    archetype: str
    capacity: int = 0
    burnout_tokens: int = 0
    status: str = "Flow"
    active_card: Optional[RainCard] = None
    sprinter_resting: bool = False
    pacing_buff: bool = False 
    atlas_cooldown: bool = False
    pending_absorb: int = 0
    assist_buff: Optional[str] = None
    peacemaker_bonus_next: bool = False
    
    # STATS & LIMITS
    min_cap: int = 0
    max_cap: int = 0
    total_burnout_gained: int = 0
    assists_used: int = 0 # LIMIT: Max 8 per game

    def init_stats(self):
        self.min_cap = self.capacity
        self.max_cap = self.capacity

    def mod_capacity(self, amount):
        self.capacity += amount
        if self.capacity < self.min_cap: self.min_cap = self.capacity
        if self.capacity > self.max_cap: self.max_cap = self.capacity

    def update_status(self):
        if self.capacity >= 10: self.status = "Flow"
        elif 5 <= self.capacity <= 9: self.status = "Strained"
        else: self.status = "Burnout"

# --- 2. CARD MANIFEST ---

def create_deck():
    # --- SHINE (Pool of 20, Game uses 12) ---
    shines_data = [
        ("Retail Therapy", 3, "You bought the thing. You didn't *need* it, but seeing it in your space makes the hard week feel worth it.", "When you treat yourself, do you usually seek comfort, status, or distraction?"),
        ("The Reunion", 4, "You see an old friend. Within five minutes, you realize you haven't laughed that hard in years.", "Who is a person from your past that you hope thinks well of you, even if you never speak again?"),
        ("The Cleared Air", 5, "A lingering misunderstanding is finally resolved. It wasn't malice; it was just a mistake.", "What is a conversation you have been dreading that would likely bring you relief if you just had it?"),
        ("The Cathartic Cry", 4, "You finally let it out. The ugly, sobbing kind. Afterwards, your chest feels lighter.", "When you are truly overwhelmed, do you tend to isolate yourself or seek out company?"),
        ("A New Passion", 5, "You started a hobby just for you. No productivity, no hustle. Just the pure joy of creating.", "If you had zero need for money or approval, how would you spend your days?"),
        ("The Pep Talk", 3, "You were spiraling, but they looked you in the eye and reminded you exactly how tough you are.", "Who is the one person in your life whose voice can actually cut through your internal panic?"),
        ("Forgiveness", 6, "You decided to let go of the grudge. The energy you spent hating them is finally yours to keep.", "Is there an apology you are waiting for that you know you will never receive? How do you make peace with that?"),
        ("The 'Big' News", 6, "A pregnancy, a promotion, a cure. Something monumental went right.", "When you get good news, do you share it immediately, or do you keep it close to protect it for a while?"),
        ("Nature's Reset", 2, "The ocean, a mountain, or just a really nice tree. You realize how small your problems are.", "What is a specific physical place you go to in your mind when you need to feel calm?"),
        ("The Unexpected Gift", 3, "It wasn't your birthday. They just saw it and thought of you. You feel known.", "What is the best gift you have ever received that wasn't expensive, but proved someone truly knew you?"),
        ("Digital Detox", 3, "You turned the phone off for 24 hours. The noise stopped. Your brain is quiet.", "If you were forced to be alone with your thoughts for 24 hours with no distractions, what would you be afraid of thinking about?"),
        ("The Inside Joke", 2, "A shared look across the room. You don't even have to say a word to know you're on the same team.", "What is a trait in a partner or friend that instantly makes you feel safe?"),
        ("Feeling 'Hot'", 2, "A good hair day, a new outfit. You catch your reflection and think, 'Damn, I've still got it.'", "When do you feel most confident: when you look good, when you achieve something, or when you help someone?"),
        ("The Volunteer", 4, "You helped someone else. Getting out of your own head healed something in you.", "What is a cause or issue that makes you feel a deep sense of responsibility?"),
        ("A Home Cooked Meal", 3, "Not takeout. Someone spent hours making this for you. It tastes like love.", "What specific meal reminds you of a time when you felt taken care of?"),
        ("Nostalgia Trip", 2, "A song or a photo album takes you back to a time when you felt safe.", "If you could revisit one specific year of your life for a day, which year would it be and why?"),
        ("The Breakthrough", 5, "That issue you've been talking about in therapy for years? It finally clicked.", "What is a hard truth about yourself that you have recently started to accept?"),
        ("Genuine Rest", 4, "Not just sleep, but rest. No alarms, no to-do lists. Your nervous system switches off.", "What does 'rest' look like to you? Is it doing nothing, or doing something you love?"),
        ("Validation", 4, "I'm proud of you. Hearing those words from the right person changes everything.", "Whose approval do you still find yourself seeking, even as an adult?"),
        ("Safe Space", 3, "A room, a person, or a moment where you don't have to perform. You can just exist.", "What version of yourself do you show the world, and how is it different from who you are when you are alone?")
    ]
    random.shuffle(shines_data)
    
    # --- DRIZZLE (24 Unique) ---
    drizzles_data = [
        ("The Doomscroll", 3, "You sat down for five minutes. An hour passed. You feel hollow and behind schedule.", "When you check out mentally, what specific emotion or thought are you usually trying to numb?"),
        ("Password Purgatory", 3, "Incorrect password. Reset link sent. 'New password cannot be old password.' Pure rage.", "What is a small, trivial inconvenience that consistently triggers a disproportionate amount of anger in you?"),
        ("Running Late", 2, "You left five minutes late, and now every red light feels like a personal attack.", "When you are late, do you tend to blame external factors or internalize it as a personal failure?"),
        ("The 'Tax'", 2, "A parking ticket. A forgotten subscription. It’s not the money; it’s the feeling of failing adulthood.", "What area of 'adulting' do you feel you are currently failing at the most?"),
        ("Notification Overload", 2, "47 unread emails. 12 Slacks. The red dots are winning.", "Does a piled-up inbox make you feel important and needed, or anxious and overwhelmed?"),
        ("Tech Glitch", 3, "The Wi-Fi drops right before the call. The printer jams. Inanimate objects are fighting you.", "How do you handle it when things don't go according to plan: do you pivot easily, or does it ruin your day?"),
        ("The Guilt Text", 2, "It’s been three days. Responding now feels like admitting failure, so you just... don't.", "Who is someone you owe a response to right now, and why does the thought of replying feel so heavy?"),
        ("Social Battery Dead", 3, "You are physically present, but your soul clocked out and went home an hour ago.", "What is your biggest 'tell' that your social battery is depleted, and do people around you respect it?"),
        ("The Cringe Memory", 2, "You were trying to sleep, but your brain decided to replay that awkward thing you said 4 years ago.", "What is a past mistake you are still punishing yourself for, long after everyone else has forgotten?"),
        ("Imposter Syndrome", 3, "You walked into the room and suddenly felt like a child wearing an adult's costume.", "In what area of your life do you feel like you are just 'faking it' right now?"),
        ("Comparison Trap", 2, "You looked at their highlight reel and suddenly your actual life feels gray and boring.", "Who is someone you compare yourself to, and what do you think they have that you lack?"),
        ("Forgot The Name", 2, "You know them. They know you. But their name is a total blank. The panic sets in.", "How comfortable are you with admitting when you don't know something or have made a mistake?"),
        ("Visual Clutter", 2, "The laundry pile. The unwashed dish. It’s a constant, silent to-do list screaming at you.", "Does your physical environment reflect your mental state, or do you keep it tidy to hide the chaos inside?"),
        ("Vague Symptom", 2, "A weird ache. You shouldn't Google it, but you will. Now you're convinced you're dying.", "When you feel vulnerable, do you tend to spiral into worst-case scenarios?"),
        ("Decision Fatigue", 3, "'What’s for dinner?' The question feels like a math test you didn't study for.", "What is a decision you are currently procrastinating on because you are afraid of making the wrong choice?"),
        ("The 'Sunday Scaries'", 3, "It’s 4 PM on a Sunday, and the shadow of Monday morning has already ruined your evening.", "What part of your upcoming week is taking up the most space in your brain right now?"),
        ("Sensory Overload", 3, "The tag on your shirt itches. The lights are too bright. The chewing noise. It's too much.", "When the world gets too loud, what is your go-to method for recalibrating?"),
        ("Unfinished Project", 2, "That hobby gear in the corner is judging you for not using it.", "Do you start things with enthusiasm and lose interest, or do you struggle to start at all?"),
        ("Passive Aggressive Email", 3, "'Per my last email.' The professional equivalent of a knife fight.", "How do you handle conflict: do you address it head-on, or do you tend to be passive-aggressive?"),
        ("Small Talk Loop", 2, "Having the exact same 'How are you?' 'Good, you?' conversation five times in an hour.", "Do you find it easier to connect with people deeply or superficially?"),
        ("The 'Check Engine' Light", 3, "A literal or metaphorical warning light you are actively choosing to ignore.", "What is a problem in your life that you are currently ignoring in hopes that it goes away?"),
        ("Diet Culture Guilt", 2, "You ate a cookie and your brain spent 20 minutes calculating how to 'pay for it.'", "How does your relationship with your body affect your daily mood?"),
        ("Noise Pollution", 2, "Construction outside. A car alarm. You can't hear your own thoughts.", "Where do you go to find silence?"),
        ("Analysis Paralysis", 3, "Too many options on the streaming service. You spend 45 minutes scrolling and watch nothing.", "Do you believe there is always a 'perfect' choice, or are you comfortable with 'good enough'?")
    ]

    # --- DOWNPOUR (24 Unique) ---
    downpours_data = [
        ("Financial Tightrope", 7, True, "Math doesn't care about your feelings. You are one emergency away from zero.", "What does 'security' mean to you, and how far away do you feel from it right now?"),
        ("The Recurring Fight", 8, True, "It started about dishes, but now you're screaming about things from 3 years ago.", "In our conflicts, what is one recurring pattern or trigger you wish we could break?"),
        ("The Depression Nest", 6, True, "The physical manifestation of your mental state. The mess is winning.", "When you are at your lowest, what is the one thing you need from a partner to feel supported?"),
        ("Total Burnout", 9, False, "You aren't just tired; you are empty. A hollow shell just going through the motions.", "If you could pause your life for one month with no consequences, what would you do with that time?"),
        ("Medical Gaslighting", 8, False, "You know something is wrong. The doctors won't listen. You feel crazy.", "Have you ever felt misunderstood by an authority figure? How did that shape your ability to advocate for yourself?"),
        ("Toxic Boss", 7, False, "Every notification triggers a fight-or-flight response. You are walking on eggshells.", "How much of your self-worth is tied to your productivity or your job title?"),
        ("Social Isolation", 5, False, "You haven't seen a friend in months. You are slowly disappearing from people's lives.", "Do you pull away from people when you are struggling, or do you reach out?"),
        ("Seasonal Depression", 6, True, "The sun went down at 4 PM and took your serotonin with it. Everything is gray.", "What is a non-negotiable routine that keeps you grounded when your mood slips?"),
        ("Creative Drought", 5, False, "You used to have ideas. Now you just have static. The well is dry.", "When you feel uninspired, do you push through the block or do you wait for motivation to return?"),
        ("Family Crisis", 7, True, "You have to go home and play the role they expect of you. It drains you to the bone.", "Which family member do you feel you have to 'perform' around the most?"),
        ("Sleep Debt", 9, False, "Reality feels brittle. You are hallucinating shadow people. You physically hurt.", "What thoughts tend to keep you awake at night?"),
        ("The Unexpected Bill", 8, True, "The car broke. The tooth broke. The bank account broke. Where will the money come from?", "How was money handled in your childhood home, and how does that affect your anxiety about bills today?"),
        ("Pet Emergency", 7, True, "The vet bill is astronomical, but you have to pay it. It's family.", "What is the hardest decision you've ever had to make regarding a dependent (pet or person)?"),
        ("Car Breakdown", 6, True, "Stranded on the side of the road. It's going to be expensive and inconvenient.", "Who is the first person you call in a crisis, and why them?"),
        ("The Leak", 6, True, "Water is dripping from the ceiling. The landlord isn't answering. Panic sets in.", "When your physical environment feels unsafe or chaotic, how does it affect your mental state?"),
        ("Data Loss", 5, False, "The hard drive failed. Years of work or memories, just gone in a blink.", "If you lost all your photos today, which specific memory would you be most terrified of forgetting?"),
        ("Credit Fraud", 7, True, "Someone bought plane tickets with your card. Now you have to fight the bank.", "How do you handle feeling violated or taken advantage of?"),
        ("Friend Breakup", 6, False, "No closure, just silence. It hurts worse than a romantic one.", "Is there a friendship you lost that you still grieve? What do you wish you had said?"),
        ("Travel Nightmare", 5, True, "Stuck in an airport for 24 hours. No sleep, expensive food, pure misery.", "How do you behave when you are physically uncomfortable and exhausted?"),
        ("Caregiver Fatigue", 8, True, "Taking care of aging parents or sick family. You have no time for yourself.", "Do you find it harder to ask for help or to accept help when it's offered?"),
        ("Jury Duty", 5, False, "It couldn't have happened at a worse time at work. A mandated pause.", "How do you handle a total lack of control over your own schedule?"),
        ("Home Infestation", 6, True, "Ants, mice, or bedbugs. Your safe space feels violated and dirty.", "What does having a 'safe space' mean to you?"),
        ("Bureaucratic Hell", 5, False, "DMV, Insurance, Taxes. On hold for 4 hours just to be hung up on.", "What is your threshold for frustration before you snap?"),
        ("Public Embarrassment", 5, False, "You went viral for the wrong reasons, or made a scene. The shame lingers.", "What is a past embarrassment that you still cringe at, and what would you tell that version of yourself now?")
    ]

    # --- HURRICANE (17 Unique - ALL JOINT) ---
    hurricanes_data = [
        ("Grief (The Empty Chair)", 13, "The world feels smaller, quieter, and wrong without them. A hole in the universe.", "How has your relationship with grief changed as you've gotten older?"),
        ("Identity Crisis", 12, "Who are you when you aren't being productive? You don't recognize yourself anymore.", "If you were stripped of your career and your roles, what would remain of you?"),
        ("The Layoff", 13, "Security is an illusion. The ground is gone. The badge doesn't work anymore.", "When the ground falls out from under you, do you panic or do you go into survival mode?"),
        ("Trust Breach", 10, "A lie was found out. The foundation cracked. Can we actually fix this?", "Is trust something that can be rebuilt once broken, or is it gone forever for you?"),
        ("Chronic Illness", 12, "It isn't going away. This isn't a phase; this is just life now.", "How do you grieve the loss of the future you thought you were going to have?"),
        ("Forced Relocation", 11, "Uprooting your life because you have no choice. You have to pack the boxes.", "What does 'home' mean to you? Is it a place, a person, or a feeling?"),
        ("Natural Disaster", 13, "Nature is indifferent to your plans. Everything you own is wet or ash. Survival mode.", "If you had 5 minutes to leave your house forever, what non-living things would you take?"),
        ("Legal Nightmare", 12, "Lawyers, paperwork, and the crushing weight of bureaucracy. The system is eating you.", "When you feel powerless against a system, do you fight back on principle or do you focus on self-preservation?"),
        ("Identity Theft", 11, "Someone else is living your life, and they ruined your credit. Recovering yourself takes time.", "How much of your identity is tied to your reputation?"),
        ("Existential Collapse", 12, "Why are we even doing this? Does any of it matter? The void stares back.", "If nothing matters, what is one reason you got out of bed today that is purely for you?"),
        ("Emergency Surgery", 13, "Life changes in a heartbeat. The waiting room is cold and smells like antiseptic.", "If you knew you might not wake up, who is the one person in your life whose voice can actually cut through your internal panic?"),
        ("The Eviction", 13, "You have 30 days to leave. Nowhere to go. The ultimate instability.", "What is your biggest fear regarding failure?"),
        ("Addiction Relapse", 12, "The demon is back. It requires everything to fight it. Trust is fragile.", "What is a coping mechanism you use that you know isn't good for you?"),
        ("The House Fire", 13, "You got out, but the memories didn't. Starting over from zero.", "How attached are you to material things, and could you start over if you had to?"),
        ("Betrayal", 11, "It wasn't a mistake. They did it on purpose. The foundation is gone.", "Do you believe in revenge, or do you believe that the best revenge is living well?"),
        ("False Accusation", 12, "You didn't do it, but proving it will cost you everything.", "What is more important to you: being right, or being at peace?"),
        ("Societal Collapse", 11, "The world outside is burning, and it's unsafe to be who you are.", "In a crisis, are you the person who takes charge, or the person who helps others emotionally?")
    ]

    # --- BUILD OBJECT LISTS ---
    
    # Shuffle Hurricane data first, so we get random scenarios, 
    # but strictly slice only 4 for the entire game.
    random.shuffle(hurricanes_data)
    active_hurricanes_data = hurricanes_data[:4]

    shines_objs = [RainCard(t, w, 0, type="Shine", flavor_text=f, scenario=s) for t, w, f, s in shines_data[:12]]
    drizzles_objs = [RainCard(t, w, 1, type="Drizzle", flavor_text=f, scenario=s) for t, w, f, s in drizzles_data]
    downpours_objs = [RainCard(t, w, 2, is_joint=j, type="Downpour", flavor_text=f, scenario=s) for t, w, j, f, s in downpours_data]
    
    # Create Objects ONLY for the 4 active hurricanes
    hurricanes_objs = [RainCard(t, w, 2, is_joint=True, type="Hurricane", flavor_text=f, scenario=s) for t, w, f, s in active_hurricanes_data]

    # --- FORCING FUNCTION: 4 HURRICANES TOTAL ---
    # We do NOT add any remaining hurricanes to the pool.
    
    # Create the pool of other cards
    filler_pool = drizzles_objs + downpours_objs + shines_objs
    random.shuffle(filler_pool)
    
    # We mix the 4 Forced Hurricanes into the first 6 filler cards.
    # This creates a "Top Deck" of 10 cards containing 4 Hurricanes.
    # Since .pop() draws from the END of the list, "Top Deck" is appended last.
    
    top_deck = hurricanes_objs + filler_pool[:6]
    random.shuffle(top_deck)
    
    bottom_deck = filler_pool[6:]
    random.shuffle(bottom_deck)
    
    final_deck = bottom_deck + top_deck
    return final_deck

def draw_card(deck):
    if not deck: deck.extend(create_deck()) 
    c = deck.pop()
    if 'card_stats' in st.session_state:
        if c.type in st.session_state.card_stats:
            st.session_state.card_stats[c.type] += 1
    return c

# --- 3. HELPER FUNCTIONS ---

def calculate_vals(player, partner):
    res_val = 0
    if player.status == "Flow": res_val = 3
    elif player.status == "Strained": res_val = 2
    elif player.status == "Burnout": res_val = 2 if player.archetype == "Soloist" else 1
    
    com_val = 0
    if player.archetype == "Peacemaker": 
        com_val = 4 # UPDATED: Base is now 4
        if partner.status == "Burnout": com_val = 5 # UPDATED: Bonus is 5
    else:
        if player.status == "Flow": com_val = 4 # UPDATED (Was 2)
        elif player.status == "Strained": com_val = 3 # UPDATED (Was 1)
        elif player.status == "Burnout": com_val = 0
    
    self_val = 0
    if player.archetype == "Soloist" and player.status == "Burnout": self_val = 1
    else:
        if player.status == "Flow": self_val = 3 # UPDATED (Was 1)
        elif player.status == "Strained": self_val = 2
        elif player.status == "Burnout": self_val = 3

    if player.peacemaker_bonus_next:
        res_val *= 2; com_val *= 2; self_val *= 2

    return {"Resolve": res_val, "Comfort": com_val, "Self-Care": self_val}

def get_assist_desc(archetype):
    if archetype == "Soloist": return "SPACE (+4 Capacity)" 
    if archetype == "Atlas": return "VALIDATION (+4 Capacity)" 
    if archetype == "Peacemaker": return "PERMISSION (+2 Capacity, Next Action Doubled)"
    if archetype == "Sprinter": return "PACING (Skip Rest)"
    return "Help"

def get_assist_name_only(archetype):
    if archetype == "Soloist": return "SPACE"
    if archetype == "Atlas": return "VALIDATION"
    if archetype == "Peacemaker": return "PERMISSION"
    if archetype == "Sprinter": return "PACING"
    return "Help"

# --- 4. STATE MANAGEMENT (UNDO LOGIC) ---

def save_checkpoint():
    st.session_state.checkpoint = {
        'p1': copy.deepcopy(st.session_state.p1),
        'p2': copy.deepcopy(st.session_state.p2),
        'deck': copy.deepcopy(st.session_state.deck),
        'turn': st.session_state.turn,
        'phase': st.session_state.phase,
        'resolved': st.session_state.resolved,
        'log': copy.deepcopy(st.session_state.log),
        'actor_queue': copy.deepcopy(st.session_state.actor_queue),
        'sprint_actions': st.session_state.sprint_actions,
        'sprinter_did_assist': st.session_state.sprinter_did_assist,
        'pending_shine': copy.deepcopy(st.session_state.pending_shine),
        'shine_actor_name': st.session_state.shine_actor_name,
        'return_to_setup': st.session_state.return_to_setup,
        'card_stats': copy.deepcopy(st.session_state.card_stats)
    }

def restore_checkpoint():
    if st.session_state.checkpoint:
        cp = st.session_state.checkpoint
        st.session_state.p1 = copy.deepcopy(cp['p1'])
        st.session_state.p2 = copy.deepcopy(cp['p2'])
        st.session_state.deck = copy.deepcopy(cp['deck'])
        st.session_state.turn = cp['turn']
        st.session_state.phase = cp['phase']
        st.session_state.resolved = cp['resolved']
        st.session_state.log = copy.deepcopy(cp['log'])
        st.session_state.actor_queue = copy.deepcopy(cp['actor_queue'])
        st.session_state.sprint_actions = cp['sprint_actions']
        st.session_state.sprinter_did_assist = cp['sprinter_did_assist']
        st.session_state.pending_shine = copy.deepcopy(cp['pending_shine'])
        st.session_state.shine_actor_name = cp['shine_actor_name']
        st.session_state.return_to_setup = cp.get('return_to_setup', False)
        if 'card_stats' in cp:
            st.session_state.card_stats = copy.deepcopy(cp['card_stats'])
        st.rerun()

# --- 5. STREAMLIT APP ---

st.set_page_config(page_title="Rain or Shine", layout="wide")

st.markdown("""
<style>
    .rain-card {
        background-color: #0E1117;
        border: 1px solid #4da6ff;
        border-radius: 10px;
        padding: 15px;
        margin-top: 15px; 
    }
    .player-card {
        background-color: #262730;
        border-radius: 10px;
        padding: 15px;
    }
    .shine-card {
        background-color: #FFF8E1;
        color: #000000;
        border: 2px solid #FFD700;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }
    .scenario-text {
        font-style: italic;
        color: #aaaaaa;
        margin-top: 8px;
        font-size: 0.9em;
        border-top: 1px solid #444;
        padding-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

if 'game_started' not in st.session_state:
    st.session_state.game_started = False
    st.session_state.log = []
    st.session_state.p1_roll = None
    st.session_state.p2_roll = None
    st.session_state.sprint_actions = 0
    st.session_state.sprinter_did_assist = False 
    st.session_state.pending_shine = None
    st.session_state.checkpoint = None 
    st.session_state.shine_actor_name = None
    st.session_state.return_to_setup = False
    st.session_state.card_stats = {"Drizzle": 0, "Downpour": 0, "Hurricane": 0, "Shine": 0}

def log(turn, msg):
    st.session_state.log.append(f"Turn {turn} | {msg}")

# --- HEADER & INFO ---
st.title("🌧️ Rain or Shine")
st.caption("A cooperative game about navigating life's stressors together.")

with st.expander("📖 Archetype Reference Guide (Click to Open)"):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**THE SOLOIST**\n* **Strength:** Effective in Burnout (Resolve 2).\n* **Weakness:** Cannot Comfort. \n* **How to Assist:** **SPACE** (+4 Capacity)") # UPDATED
        st.markdown("**THE SPRINTER**\n* **Strength:** Special Ability: **SPRINT** (Can take 2 Actions in 1 turn).\n* **Weakness:** Must Rest next turn (Active Recovery: +1 Capacity).\n* **How to Assist:** **PACING** (Skip Rest)")
    with c2:
        st.markdown("**THE ATLAS**\n* **Strength:** Special Ability: **ABSORB** (Can absorb up to 2 damage for partner).\n* **Weakness:** Cannot absorb 2 turns in a row.\n* **How to Assist:** **VALIDATION** (+4 Capacity)") # UPDATED
        st.markdown("**THE PEACEMAKER**\n* **Strength:** Comfort always 3 (4 if partner in Burnout).\n* **Weakness:** Empath (Lose 1 Capacity if partner takes 3+ dmg).\n* **How to Assist:** **PERMISSION** (+2 Capacity, Next Action Doubled)")

# --- SIDEBAR: SETUP & UNDO ---
with st.sidebar:
    if not st.session_state.game_started:
        st.header("New Game Setup")
        
        # Player 1
        st.subheader("Player 1")
        n1 = st.text_input("Name", "Kevin")
        a1 = st.selectbox("Role", ["Soloist", "Sprinter", "Atlas", "Peacemaker"], key="r1")
        
        if st.session_state.p1_roll is None:
            if st.button(f"Roll 2d6 for {n1}"):
                roll = random.randint(1,6) + random.randint(1,6)
                st.session_state.p1_roll = max(1, roll)
                st.rerun()
        else:
            st.success(f"Rolled: {st.session_state.p1_roll}")

        st.markdown("---")

        # Player 2
        st.subheader("Player 2")
        n2 = st.text_input("Name", "Partner")
        a2 = st.selectbox("Role", ["Soloist", "Sprinter", "Atlas", "Peacemaker"], key="r2")
        
        if st.session_state.p2_roll is None:
            if st.button(f"Roll 2d6 for {n2}"):
                roll = random.randint(1,6) + random.randint(1,6)
                st.session_state.p2_roll = max(1, roll)
                st.rerun()
        else:
            st.success(f"Rolled: {st.session_state.p2_roll}")
        
        st.markdown("---")

        if st.session_state.p1_roll and st.session_state.p2_roll:
            if st.button("Start Game"):
                st.session_state.p1 = Player(n1, a1, capacity=st.session_state.p1_roll)
                st.session_state.p2 = Player(n2, a2, capacity=st.session_state.p2_roll)
                st.session_state.p1.init_stats()
                st.session_state.p2.init_stats()
                st.session_state.p1.update_status()
                st.session_state.p2.update_status()
                
                # Deck Creation & Stacking
                full_deck = create_deck()
                
                # Extract 2 Drizzles for Setup
                setup_cards = []
                temp_storage = []
                
                # Note: Because we stacked Hurricanes at the TOP (end of list), 
                # we must be careful not to pop them if we are looking for Drizzles.
                # This loop handles it by putting non-drizzles into temp_storage
                # and then putting them back.
                
                while len(setup_cards) < 2 and full_deck:
                    c = full_deck.pop()
                    if c.type == "Drizzle":
                        setup_cards.append(c)
                    else:
                        temp_storage.append(c)
                
                for c in reversed(temp_storage):
                    full_deck.append(c)
                
                st.session_state.deck = full_deck
                st.session_state.p1.active_card = setup_cards[0]
                st.session_state.p2.active_card = setup_cards[1]

                st.session_state.card_stats["Drizzle"] += 2
                
                st.session_state.resolved = 0
                st.session_state.turn = 1
                st.session_state.phase = "Strategy" 
                st.session_state.actor_queue = [] 
                st.session_state.game_started = True
                st.session_state.checkpoint = None
                st.rerun()
    else:
        st.metric("Resolved", f"{st.session_state.resolved}/10")
        st.metric("Turn", st.session_state.turn)
        
        if st.session_state.checkpoint:
            if st.button("↩️ Undo Last Action"):
                restore_checkpoint()

        st.markdown("---")
        if st.button("Reset Game"):
            st.session_state.clear()
            st.rerun()

# --- MAIN WINDOW ---
if st.session_state.game_started:
    
    p1 = st.session_state.p1
    p2 = st.session_state.p2

    # GAME OVER LOGIC
    game_over = False
    victory = False
    fail_msg = ""
    
    if p1.capacity <= 0:
        game_over = True
        fail_msg = f"{p1.name} ran out of emotional capacity."
    elif p2.capacity <= 0:
        game_over = True
        fail_msg = f"{p2.name} ran out of emotional capacity."
    elif p1.burnout_tokens >= 3:
        game_over = True
        fail_msg = f"{p1.name} accumulated too much Burnout."
    elif p2.burnout_tokens >= 3:
        game_over = True
        fail_msg = f"{p2.name} accumulated too much Burnout."
    
    if st.session_state.resolved >= 10:
        game_over = True
        victory = True

    if game_over:
        if victory:
            st.balloons()
            st.success("🎉 **VICTORY!** You have resolved 10 Rain Cards together!")
        else:
            st.error(f"💀 **GAME OVER:** {fail_msg}")
        
        # --- STATISTICS REPORT ---
        st.subheader("📊 Game Statistics")
        cs = st.session_state.card_stats
        
        report = []
        report.append(f"GAME RESULT: {'VICTORY' if victory else 'DEFEAT'}")
        report.append(f"REASON: {fail_msg if not victory else 'Resolved 10 Cards'}")
        report.append("-" * 30)
        report.append(f"PLAYER STATS")
        report.append(f"{p1.name} ({p1.archetype}):")
        report.append(f"  - Capacity: Start {st.session_state.p1_roll}, End {p1.capacity}")
        report.append(f"  - High/Low Cap: {p1.max_cap} / {p1.min_cap}")
        report.append(f"  - Total Burnout Accumulated: {p1.total_burnout_gained}")
        report.append(f"  - Assists Used: {p1.assists_used}/8")
        report.append("")
        report.append(f"{p2.name} ({p2.archetype}):")
        report.append(f"  - Capacity: Start {st.session_state.p2_roll}, End {p2.capacity}")
        report.append(f"  - High/Low Cap: {p2.max_cap} / {p2.min_cap}")
        report.append(f"  - Total Burnout Accumulated: {p2.total_burnout_gained}")
        report.append(f"  - Assists Used: {p2.assists_used}/8")
        report.append("-" * 30)
        report.append(f"CARDS DRAWN")
        report.append(f"  Drizzle: {cs['Drizzle']}")
        report.append(f"  Downpour: {cs['Downpour']}")
        report.append(f"  Hurricane: {cs['Hurricane']}")
        report.append(f"  Shine: {cs['Shine']}")
        report.append("-" * 30)
        report.append("FULL GAME LOG:")
        
        for line in st.session_state.log:
            report.append(line)
            
        full_text = "\n".join(report)
        st.text_area("Copy Game Log & Stats", value=full_text, height=400)
        
        if st.button("Play Again"):
            st.session_state.clear()
            st.rerun()
        st.stop()

    st.info("💀 **Game Over if:** Any player reaches **0 Capacity** OR accumulates **3 Burnout Tokens**.")

    turn = st.session_state.turn

    # 1. PLAYER DASHBOARD
    col1, col2 = st.columns(2)
    def render_p(player, col, is_acting):
        with col:
            border = "2px solid #FF4B4B" if is_acting else "1px solid #333"
            
            assists_left = 8 - player.assists_used
            
            st.markdown(f"""
            <div style="border:{border};" class="player-card">
                <h3>{player.name} ({player.archetype})</h3>
                <p style="font-size:1.2em;">Capacity: <b>{player.capacity}</b> | Status: <b>{player.status}</b></p>
                <p style="font-size:0.9em; color:#aaa;">Assists Left: {assists_left}/8</p>
            </div>
            """, unsafe_allow_html=True)
            
            if player.burnout_tokens > 0: st.error(f"💀 Tokens: {player.burnout_tokens}/3")
            if player.assist_buff: st.info(f"✨ Assisted ({player.assist_buff})")
            if player.sprinter_resting: st.warning("💤 RECOVERY TURN")
            if player.pending_absorb > 0: st.info(f"🛡️ Absorb Queued: {player.pending_absorb}")
            
            if player.active_card:
                c = player.active_card
                tags = ""
                if c.is_joint: tags += "<span style='background-color:#5c5cff; color:white; padding:2px 6px; border-radius:4px; margin-right:5px;'>🤝 Joint</span>"
                if c.accumulated_tokens > 0: tags += f"<span style='background-color:#521818; color:white; padding:2px 6px; border-radius:4px;'>🔥 Stress: +{c.accumulated_tokens}</span>"
                if tags: tags = "<br>" + tags
                
                st.markdown(f"""
                <div class="rain-card">
                    <h4>⛈ {c.title} <small>({c.type})</small></h4>
                    <p><i>"{c.flavor_text}"</i></p>
                    <p class="scenario-text">🤔 {c.scenario}</p>
                    <p>Weight: <b>{c.weight}</b> | Exhaust: <b>-{c.exhaust}</b> {tags}</p>
                </div>
                """, unsafe_allow_html=True)
            else: 
                st.success("☀️ Clear Skies")

    active_id = st.session_state.actor_queue[0] if (st.session_state.phase == "Action" and st.session_state.actor_queue) else None
    active_name_str = p1.name if active_id == "p1" else (p2.name if active_id == "p2" else "")
    
    render_p(p1, col1, p1.name == active_name_str)
    render_p(p2, col2, p2.name == active_name_str)
    
    st.divider()

    # 2. PHASE LOGIC
    st.header(f"Phase: {st.session_state.phase}")

    # --- SHINE RESOLUTION ---
    if st.session_state.phase == "Shine":
        shine = st.session_state.pending_shine
        actor_name_str = st.session_state.shine_actor_name
        actor = p1 if actor_name_str == "p1" else p2
        
        st.markdown(f"""
        <div class="shine-card">
            <h2>☀️ {shine.title}</h2>
            <p><i>"{shine.flavor_text}"</i></p>
            <p class="scenario-text"><b>Reflect:</b> {shine.scenario}</p>
            <h3>+{shine.weight} Capacity</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Claim Shine & Redraw"):
            save_checkpoint() 
            old_cap = actor.capacity
            actor.mod_capacity(shine.weight)
            log(turn, f"{actor.name} ({actor.archetype}) claims {shine.title}. Capacity {old_cap} -> {actor.capacity}.")
            
            new_c = draw_card(st.session_state.deck)
            if new_c.type == "Shine":
                st.session_state.pending_shine = new_c
                st.rerun() 
            else:
                actor.active_card = new_c
                st.session_state.pending_shine = None
                
                if st.session_state.return_to_setup:
                    st.session_state.phase = "Setup"
                    st.session_state.return_to_setup = False
                elif st.session_state.sprint_actions > 0:
                    st.session_state.phase = "Action"
                elif st.session_state.actor_queue:
                    st.session_state.phase = "Action"
                else:
                    st.session_state.phase = "Atlas_Intervention"
                st.rerun()

    # --- SETUP PHASE ---
    elif st.session_state.phase == "Setup":
        if p1.active_card is None:
            c = draw_card(st.session_state.deck)
            if c.type == "Shine":
                st.session_state.pending_shine = c
                st.session_state.shine_actor_name = "p1"
                st.session_state.phase = "Shine"
                st.session_state.return_to_setup = True
                st.rerun()
            else:
                p1.active_card = c
                st.rerun()
        
        if p2.active_card is None:
            c = draw_card(st.session_state.deck)
            if c.type == "Shine":
                st.session_state.pending_shine = c
                st.session_state.shine_actor_name = "p2"
                st.session_state.phase = "Shine"
                st.session_state.return_to_setup = True
                st.rerun()
            else:
                p2.active_card = c
                st.rerun()

        st.session_state.phase = "Strategy"
        st.rerun()

    # --- STRATEGY PHASE ---
    elif st.session_state.phase == "Strategy":
        st.write("### 🗣️ Discuss: Who should act first this turn?")
        c1, c2 = st.columns(2)
        if c1.button(f"1. {p1.name} goes first"):
            save_checkpoint() 
            st.session_state.actor_queue = ["p1", "p2"] 
            st.session_state.phase = "Action"
            st.rerun()
        if c2.button(f"1. {p2.name} goes first"):
            save_checkpoint() 
            st.session_state.actor_queue = ["p2", "p1"] 
            st.session_state.phase = "Action"
            st.rerun()
        
        st.markdown("---")
        
        # VISUAL CONNECTION BOX (DISABLED)
        with st.expander("🕊️ Connection Opportunity (Disabled in Prototype)"):
            st.caption("This mechanic is visually present but disabled for this test.")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                if p1.active_card: st.write(f"**Topic:** {p1.active_card.title}")
            with c_p2:
                if p2.active_card: st.write(f"**Topic:** {p2.active_card.title}")

    # --- ACTION PHASE ---
    elif st.session_state.phase == "Action":
        if not st.session_state.actor_queue:
            st.session_state.phase = "Atlas_Intervention"
            st.rerun()
        
        actor_id = st.session_state.actor_queue[0]
        actor = st.session_state.p1 if actor_id == "p1" else st.session_state.p2
        partner = st.session_state.p2 if actor_id == "p1" else st.session_state.p1
        
        st.subheader(f"⚡ {actor.name}'s Action")
        if st.session_state.sprint_actions > 0:
            st.info(f"🏃 Sprinting: {st.session_state.sprint_actions} Action(s) Remaining")

        if actor.sprinter_resting and st.session_state.sprint_actions == 0:
            if st.button("💤 Active Recovery (+1 Capacity)"):
                save_checkpoint() 
                old_cap = actor.capacity
                actor.mod_capacity(1)
                actor.sprinter_resting = False
                log(turn, f"{actor.name} ({actor.archetype}) takes Active Recovery. Capacity {old_cap} -> {actor.capacity}.")
                st.session_state.actor_queue.pop(0)
                st.rerun()
        else:
            vals = calculate_vals(actor, partner)
            opts = []
            
            if actor.active_card: opts.append(f"Resolve my Rain Card (-{vals['Resolve']} Weight)")
            else: opts.append("Resolve (No Card - Invalid)")
                
            if partner.active_card:
                if actor.archetype == "Soloist" and actor.status != "Flow": opts.append("Resolve Partner (LOCKED: Soloist needs Flow)")
                else: opts.append(f"Resolve {partner.name}'s Rain Card (-{vals['Resolve']} Weight)")
            else: opts.append("Resolve Partner (No Card)")

            if actor.archetype == "Soloist":
                opts.append("Comfort Partner (LOCKED: Soloist Weakness)")
            elif vals['Comfort'] > 0: 
                opts.append(f"Comfort {partner.name} (+{vals['Comfort']} Capacity)")
            else: 
                opts.append("Comfort Partner (LOCKED: Burnout)")

            opts.append(f"Self-Care (+{vals['Self-Care']} Capacity)")
            
            if not st.session_state.sprinter_did_assist:
                if actor.assists_used < 8:
                    charges = 8 - actor.assists_used
                    opts.append(f"Assist {partner.name} (Effect: {get_assist_desc(partner.archetype)}) - {charges}/8 Left")
                else:
                    opts.append("Assist (LOCKED: 0/8 Charges)")

            if actor.archetype == "Sprinter" and st.session_state.sprint_actions == 0:
                opts.append("⚡ SPRINT (Perform 2 Actions)")
            
            with st.form("act"):
                if actor.peacemaker_bonus_next:
                    st.info("✨ **PERMISSION ACTIVE:** Your next action (except Assist/Sprint) is Doubled!")
                
                choice = st.radio("Choose Action:", opts)
                
                if st.form_submit_button("Confirm"):
                    save_checkpoint() 
                    
                    if "LOCKED" in choice or "Invalid" in choice or "No Card" in choice:
                        st.error("Invalid Selection.")
                        st.stop()

                    if "SPRINT" in choice:
                        st.session_state.sprint_actions = 2
                        if actor.pacing_buff:
                            actor.pacing_buff = False
                            log(turn, f"🏃 {actor.name} uses PACING to Sprint without fatigue!")
                        else:
                            actor.sprinter_resting = True
                        log(turn, f"{actor.name} ({actor.archetype}) activates SPRINT! (2 Actions).")
                        st.rerun()

                    card_resolved = False
                    consumed_bonus = False
                    
                    if "Resolve my Rain" in choice:
                        old_w = actor.active_card.weight
                        actor.active_card.weight -= vals['Resolve']
                        log(turn, f"{actor.name} ({actor.archetype}) resolves '{actor.active_card.title}'. Weight {old_w} -> {actor.active_card.weight}.")
                        if actor.active_card.weight <= 0:
                            
                            bonus = 0
                            if actor.active_card.type == "Downpour": bonus = 1
                            elif actor.active_card.type == "Hurricane": bonus = 2
                            
                            actor.active_card = None 
                            st.session_state.resolved += 1
                            
                            if bonus > 0:
                                actor.mod_capacity(bonus)
                                log(turn, f"✅ Card Resolved! {actor.name} gets +{bonus} Capacity.")
                            else:
                                log(turn, f"✅ Card Resolved! (No Bonus).")
                                
                            card_resolved = True
                        consumed_bonus = True

                    elif "Resolve" in choice and partner.name in choice:
                        old_w = partner.active_card.weight
                        partner.active_card.weight -= vals['Resolve']
                        log(turn, f"{actor.name} ({actor.archetype}) resolves partner's '{partner.active_card.title}'. Weight {old_w} -> {partner.active_card.weight}.")
                        if partner.active_card.weight <= 0:
                            
                            bonus = 0
                            if partner.active_card.type == "Downpour": bonus = 1
                            elif partner.active_card.type == "Hurricane": bonus = 2
                            
                            partner.active_card = None 
                            st.session_state.resolved += 1
                            
                            if bonus > 0:
                                partner.mod_capacity(bonus)
                                log(turn, f"✅ Card Resolved! {partner.name} gets +{bonus} Capacity.")
                            else:
                                log(turn, f"✅ Card Resolved! (No Bonus).")
                                
                            card_resolved = True
                        consumed_bonus = True

                    elif "Comfort" in choice:
                        old_cap = partner.capacity
                        partner.mod_capacity(vals['Comfort'])
                        log(turn, f"{actor.name} ({actor.archetype}) COMFORTS {partner.name}. {partner.name} Capacity {old_cap} -> {partner.capacity}.")
                        consumed_bonus = True

                    elif "Self-Care" in choice:
                        old_cap = actor.capacity
                        actor.mod_capacity(vals['Self-Care'])
                        log(turn, f"{actor.name} ({actor.archetype}) SELF-CARES. Capacity {old_cap} -> {actor.capacity}.")
                        # REMOVED: Soloist penalty
                        consumed_bonus = True

                    elif "Assist" in choice:
                        actor.assists_used += 1
                        if st.session_state.sprint_actions > 0: st.session_state.sprinter_did_assist = True
                        
                        assist_name = get_assist_name_only(partner.archetype)
                        p_old = partner.capacity
                        
                        # UPDATED ASSIST VALUES HERE
                        if partner.archetype == "Soloist": partner.mod_capacity(4); partner.assist_buff="Space"
                        elif partner.archetype == "Atlas": partner.mod_capacity(4); partner.assist_buff="Validation"
                        elif partner.archetype == "Peacemaker": 
                            partner.mod_capacity(2); 
                            partner.peacemaker_bonus_next=True 
                            partner.assist_buff="Permission"
                        elif partner.archetype == "Sprinter": 
                            partner.assist_buff="Pacing"
                            partner.pacing_buff = True
                            partner.sprinter_resting = False
                        
                        log(turn, f"{actor.name} ({actor.archetype}) ASSISTS {partner.name} ({partner.archetype}) with {assist_name}. {partner.name} Capacity {p_old} -> {partner.capacity}. (Charges: {actor.assists_used}/8)")

                    if actor.peacemaker_bonus_next and consumed_bonus:
                        actor.peacemaker_bonus_next = False
                    
                    if st.session_state.sprint_actions > 0:
                        st.session_state.sprint_actions -= 1

                    if st.session_state.sprint_actions == 0:
                        st.session_state.actor_queue.pop(0)
                        st.session_state.sprinter_did_assist = False 
                    
                    st.rerun()

    # --- ATLAS INTERVENTION PHASE ---
    elif st.session_state.phase == "Atlas_Intervention":
        atlas_player = None
        partner_player = None
        if p1.archetype == "Atlas" and not p1.atlas_cooldown: 
            atlas_player = p1
            partner_player = p2
        elif p2.archetype == "Atlas" and not p2.atlas_cooldown: 
            atlas_player = p2
            partner_player = p1
        
        pending_dmg = 0
        if partner_player and partner_player.active_card:
            pending_dmg = partner_player.active_card.exhaust_value()
        
        if atlas_player and atlas_player.active_card and atlas_player.active_card.is_joint:
             pending_dmg += 1

        if atlas_player and pending_dmg > 0:
            st.info(f"🛡️ {atlas_player.name} (Atlas) Opportunity: Partner is about to take ~{pending_dmg} damage.")
            with st.form("atlas_absorb"):
                max_absorb = min(2, pending_dmg)
                amt = st.slider("Select Absorb Amount", 0, max_absorb, 0)
                
                if st.form_submit_button("Confirm"):
                    save_checkpoint() 
                    atlas_player.pending_absorb = amt
                    if amt > 0: log(turn, f"🛡️ {atlas_player.name} prepares to ABSORB {amt} damage for {partner_player.name}.")
                    st.session_state.phase = "Exhaust"
                    st.rerun()
        else:
            st.session_state.phase = "Exhaust"
            st.rerun()

    # --- EXHAUST PHASE ---
    elif st.session_state.phase == "Exhaust":
        st.info("🌙 End of Turn: Calculating Exhaust & Stress")
        
        if st.button("End Turn"):
            st.session_state.checkpoint = None 
            
            d1 = 0
            if p1.active_card: d1 = p1.active_card.exhaust_value()
            d2 = 0
            if p2.active_card: d2 = p2.active_card.exhaust_value()
            
            if p1.pending_absorb > 0:
                d1 += p1.pending_absorb; d2 -= p1.pending_absorb
                p1.atlas_cooldown = True; p1.pending_absorb = 0
            else: p1.atlas_cooldown = False
                
            if p2.pending_absorb > 0:
                d2 += p2.pending_absorb; d1 -= p2.pending_absorb
                p2.atlas_cooldown = True; p2.pending_absorb = 0
            else: p2.atlas_cooldown = False

            if d1 < 0: d1 = 0
            if d2 < 0: d2 = 0

            s1 = 1 if (p2.active_card and p2.active_card.is_joint) else 0
            s2 = 1 if (p1.active_card and p1.active_card.is_joint) else 0
            
            if p1.archetype == "Peacemaker" and d2 >= 3:
                p1.mod_capacity(-1)
                log(turn, f"💔 {p1.name} (Peacemaker) feels pain from partner's high damage. (-1 Capacity)")
            else: 
                d1 += s1 

            if p2.archetype == "Peacemaker" and d1 >= 3:
                p2.mod_capacity(-1)
                log(turn, f"💔 {p2.name} (Peacemaker) feels pain from partner's high damage. (-1 Capacity)")
            else: 
                d2 += s2 

            if p1.archetype == "Atlas" and p1.status == "Flow" and d1 > 0: 
                d1 -= 1
                log(turn, f"🛡️ {p1.name} (Atlas) Pain Tolerance reduces damage by 1.")

            if p2.archetype == "Atlas" and p2.status == "Flow" and d2 > 0: 
                d2 -= 1
                log(turn, f"🛡️ {p2.name} (Atlas) Pain Tolerance reduces damage by 1.")

            if d1 > 0:
                old_c = p1.capacity
                p1.mod_capacity(-d1)
                log(turn, f"💥 {p1.name} takes {d1} Exhaust Damage. Capacity {old_c} -> {p1.capacity}.")
            else:
                log(turn, f"🛡️ {p1.name} takes 0 damage.")

            if d2 > 0:
                old_c = p2.capacity
                p2.mod_capacity(-d2)
                log(turn, f"💥 {p2.name} takes {d2} Exhaust Damage. Capacity {old_c} -> {p2.capacity}.")
            else:
                log(turn, f"🛡️ {p2.name} takes 0 damage.")

            p1.update_status(); p2.update_status()
            
            for p in [p1, p2]:
                if p.archetype == "Sprinter" and p.pacing_buff:
                    p.assist_buff = "Pacing" 
                elif p.archetype == "Peacemaker" and p.peacemaker_bonus_next:
                    p.assist_buff = "Permission" 
                else:
                    p.assist_buff = None 
                
                if p.status == "Burnout": 
                    p.burnout_tokens += 1
                    p.total_burnout_gained += 1
                else: p.burnout_tokens = 0
                
                if p.active_card:
                    p.active_card.age += 1
                    if p.active_card.age >= 3: 
                        p.active_card.accumulated_tokens += 1
                        log(turn, f"⚠️ STRESS ACCUMULATED: {p.name}'s card rots! +1 Token (Total: {p.active_card.accumulated_tokens})")
            
            st.session_state.turn += 1
            st.session_state.phase = "Setup" 
            st.rerun()

    st.divider()
    st.caption("Game Log")
    for m in reversed(st.session_state.log): st.text(f"> {m}")