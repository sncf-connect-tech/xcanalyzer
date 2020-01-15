//
//  Uses.swift
//  SampleCore
//
//  Created by Deffrasnes Ghislain on 14/06/2019.
//  Copyright © 2019 E-Voyageurs Technologies. All rights reserved.
//

import Foundation

class Uses {

    private class SubClass: MySwiftClass {

    }

    private let member: MySwiftClass
    private let memberOptional: MySwiftClass?
    private var memberVar: MySwiftClass
    private var memberOptionalVar: MySwiftClass?

    init() {
        self.member = MySwiftClass()
        self.memberOptional = nil
        self.memberVar = MySwiftClass()

        print(MySwiftClass())

        let myInstance = MySwiftClass()
        print(myInstance)

        let myInstance2: MySwiftClass
        myInstance2 = MySwiftClass()
        print(myInstance2)

        var myInstance3 = MySwiftClass()
        print(myInstance3)

        var myInstance4: MySwiftClass
        myInstance4 = MySwiftClass()
        print(myInstance4)

        let myInstance5: MySwiftClass?
        var myInstance6: MySwiftClass?
    }

    func inMethod(argument: MySwiftClass) -> MySwiftClass {
        let insideMethodInstantiation = MySwiftClass()
        print(insideMethodInstantiation)

        let insideMethodTypeDef: MySwiftClass
        insideMethodTypeDef = MySwiftClass()

        let insideMethodTypeDefOptional: MySwiftClass?
        insideMethodTypeDefOptional = nil
        if let insideMethodTypeDefOptional = insideMethodTypeDefOptional {
            print(insideMethodTypeDefOptional)
        }

        MySwiftClass.staticMethod()
        MySwiftClass.classMethod()

        return insideMethodTypeDef
    }

    func otherMethod() -> MySwiftClass {
        return MySwiftClass()
    }

    func otherMethodOptional() -> MySwiftClass? {
        return MySwiftClass()
    }

    func withTypeInference() {
        let myVar = otherMethod()
        let myVarOptional = otherMethodOptional()

        print(myVar)

        if let myVarOptional = myVarOptional {
            print(myVarOptional)
        }
    }

}

extension MySwiftClass {

}
