#include <general-utils>
#include <mouse-utils>

#SingleInstance Force
#NoEnv

SendMode Input
SetWorkingDir %A_ScriptDir%

MouseClickWindowHuman(x_window_ratio, y_window_ratio, x_range, y_range){
    global mouse_navigator
    mouse_navigator.MouseClickWindowHuman(x_window_ratio, y_window_ratio, x_range, y_range)
}

ClickHandPosition6(Pos){
    switch Pos{
        case 1: MouseClickWindowHuman(0.389516, 0.927000, 0.01, 0.05)
        case 2: MouseClickWindowHuman(0.431452, 0.927000, 0.01, 0.05)
        case 3: MouseClickWindowHuman(0.465726, 0.927000, 0.01, 0.05)
        case 4: MouseClickWindowHuman(0.518145, 0.927000, 0.01, 0.05)
        case 5: MouseClickWindowHuman(0.553226, 0.927000, 0.01, 0.05)
        case 6: MouseClickWindowHuman(0.610887, 0.927000, 0.01, 0.05)
        default: MsgBox, ERROR: Function 'ClickHandPosition6' got unexpected Pos '%Pos%'. 
    }
}

ClickHandPosition5(Pos){
    switch Pos{
        case 1: MouseClickWindowHuman(0.387097, 0.927000, 0.01, 0.05)
        case 2: MouseClickWindowHuman(0.440323, 0.927000, 0.01, 0.05)
        case 3: MouseClickWindowHuman(0.488710, 0.927000, 0.01, 0.05)
        case 4: MouseClickWindowHuman(0.542339, 0.927000, 0.01, 0.05)
        case 5: MouseClickWindowHuman(0.608871, 0.927000, 0.01, 0.05)
        default: MsgBox, ERROR: Function 'ClickHandPosition5' got unexpected Pos '%Pos%'. 
    }
}

ClickHandPosition4(Pos){
    switch Pos{
        case 1: MouseClickWindowHuman(0.396635, 0.916896, 0.01, 0.05)
        case 2: MouseClickWindowHuman(0.468349, 0.914148, 0.01, 0.05)
        case 3: MouseClickWindowHuman(0.542869, 0.905220, 0.01, 0.05)
        case 4: MouseClickWindowHuman(0.608173, 0.912775, 0.01, 0.05)
        default: MsgBox, ERROR: Function 'ClickHandPosition4' got unexpected Pos '%Pos%'. 
    }
}

PlayFromHand(Pos, NumInHand){
    ;; TODO: handle position > numInHand
    switch NumInHand{
        case 6: ClickHandPosition6(Pos)
        case 5: ClickHandPosition5(Pos)
        case 4: ClickHandPosition4(Pos)
        case 3: ClickHandPosition5(Pos+1)
        case 2: ClickHandPosition4(Pos+1)
        case 1: ClickHandPosition5(Pos+2)
        default: MsgBox, ERROR: Function 'PlayFromHand' got unexpected NumInHand '%NumInHand%'. 
    }
    SleepRandom(300)
    MouseClickWindowHuman(0.217949, 0.364011, 0.1, 0.1) ; play on board to left of minions
    SleepRandom(300)
}

PlayFromHandPhase(CardPos1, CardPos2, CardPos3, NumInHand:=6){
    ;; TODO: handle throw if inputs equal
    CardPos2Adjusted := CardPos3 < CardPos2 ? CardPos2 - 1 : CardPos2
    if(CardPos3 < CardPos1){
        CardPos1Adjusted := CardPos2 < CardPos1 ? CardPos1 - 2 : CardPos1 - 1
    }else{
        CardPos1Adjusted := CardPos2 < CardPos1 ? CardPos1 - 1 : CardPos1
    }
    PlayFromHand(CardPos3, NumInHand)
    PlayFromHand(CardPos2Adjusted, NumInHand-1)
    PlayFromHand(CardPos1Adjusted, NumInHand-2)
    SleepRandom(200)
    PressReady()
    SleepRandom(6000)
}

ClickFriendlyMinion3(Pos){
    switch Pos{
        case 1: MouseClickWindowHuman(0.441129, 0.670000, 0.01, 0.05)
        case 2: MouseClickWindowHuman(0.481452, 0.670000, 0.01, 0.05)
        case 3: MouseClickWindowHuman(0.564919, 0.670000, 0.01, 0.05)
        default: MsgBox, ERROR: Function 'ClickFriendlyMinion3' got unexpected Pos '%Pos%'. 
    }
    SleepRandom(200)
}

ClickFriendlyMinion(NumFriendlyMinions, Pos){
    switch NumFriendlyMinions{
        case 3: ClickFriendlyMinion3(Pos)
        default: MsgBox, ERROR: Function 'ClickFriendlyMinion' got unexpected NumFriendlyMinions '%NumFriendlyMinions%'. 
    }
}

PressReady(){
    MouseClickWindowHuman(0.824194, 0.454481, 0.01, 0.02)
    SleepRandom(200)
    MouseClickWindowHuman(0.824194, 0.454481, 0.01, 0.02)
}

ChooseEnemyTarget(NumEnemies, Pos){
    switch Pos{
        case 1: MouseClickWindowHuman(0.441129, 0.276000, 0.01, 0.05)
        case 2: MouseClickWindowHuman(0.481452, 0.276000, 0.01, 0.05)
        case 3: MouseClickWindowHuman(0.564919, 0.276000, 0.01, 0.05)
        default: MsgBox, ERROR: Function 'ChooseEnemyTarget' got unexpected Pos '%Pos%'. 
    }
}

ChooseUntargetedAttack(PosAttack){
    switch PosAttack{
        case 1: MouseClickWindowHuman(0.397177, 0.451658, 0.03, 0.03)
        case 2: MouseClickWindowHuman(0.495565, 0.451658, 0.03, 0.03)
        case 3: MouseClickWindowHuman(0.597177, 0.449541, 0.03, 0.03)
        case 4: MouseClickWindowHuman(0.697177, 0.449541, 0.03, 0.03)
        default: MsgBox, ERROR: Function 'ChooseUntargetedAttack' got unexpected PosAttack '%PosAttack%'. 
    }
    SleepRandom(1500)
}

ChooseEnemyTargetedAttack(PosAttack, PosEnemy){
    switch PosAttack{
        case 1: MouseClickWindowHuman(0.397177, 0.451658, 0.03, 0.03)
        case 2: MouseClickWindowHuman(0.495565, 0.451658, 0.03, 0.03)
        case 3: MouseClickWindowHuman(0.597177, 0.449541, 0.03, 0.03)
        default: MsgBox, ERROR: Function 'ChooseEnemyTargetedAttack' got unexpected Pos '%PosAttack%'. 
    }
    SleepRandom(500)
    ChooseEnemyTarget(3, PosEnemy)
    SleepRandom(1000)
}

ChooseFriendlyTargetedAttack(PosAttack, PosFriendly){
    switch PosAttack{
        case 1: MouseClickWindowHuman(0.397177, 0.451658, 0.05, 0.05)
        case 2: MouseClickWindowHuman(0.495565, 0.451658, 0.05, 0.05)
        case 3: MouseClickWindowHuman(0.597177, 0.449541, 0.05, 0.05)
        default: MsgBox, ERROR: Function 'ChooseFriendlyTargetedAttack' got unexpected Pos '%PosAttack%'. 
    }
    SleepRandom(500)
    ClickFriendlyMinion(3, PosFriendly)
    SleepRandom(1000)
}

SpeedupAnimations(loops){
    Loop, %loops%{
        SleepRandom(300)
        MouseClickWindowHuman(0.217949, 0.364011, 0.05, 0.05)
    }
}

FireFarm(){
    ChooseUntargetedAttack(2) ;; rag
    ChooseUntargetedAttack(2) ;; baron
    ChooseEnemyTargetedAttack(1, 2) ;; anton
}

;;;; cmd line parsing
args_allowable := ["--play", "--attack"]
play := FALSE
attack := FALSE

for n, cmd_args in A_Args{
    if(not HasVal(args_allowable, cmd_args)){
        MsgBox ERROR: illegal cmd arg '%cmd_args%'.
        ExitApp 1
    }
    if(cmd_args = "--play"){
        play := TRUE
    }
    if(cmd_args = "--attack"){
        attack := TRUE
    }
}

;;;; locate hearthstone and bring it to the foreground
SetTitleMatchMode, 2
CoordMode, Mouse, Screen
tt = Hearthstone ahk_class UnityWndClass
WinWait, %tt%
IfWinNotActive, %tt%,, WinActivate, %tt%

;;;; store dimensions of hearthstone in mouse navigator object
WinGetPos, x_window_ratio, y_window_ratio, x_range, y_range, Hearthstone
mouse_navigator := new MouseWindowNavigator(x_window_ratio, y_window_ratio, x_range, y_range)

if(play){
    PlayFromHandPhase(1, 2, 3)
}

if(attack){
    ;ChooseEnemyTargetedAttack(1, 3)
    ;ChooseEnemyTargetedAttack(2, 2)
    ;ChooseUntargetedAttack(2)

    FireFarm()

    PressReady()
    SpeedupAnimations(40)
}

RButton::ExitApp
Esc::ExitApp
