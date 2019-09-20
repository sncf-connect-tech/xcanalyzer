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

    init() {
        self.member = MySwiftClass()
        self.memberOptional = nil
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
