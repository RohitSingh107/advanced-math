use borsh::{BorshDeserialize, BorshSerialize};

use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
};

use crate::calculator::CalculatorInstructions;
mod calculator;

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct Calculator {
    pub value : u32,
}

entrypoint!(process_instruction);

fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {

    msg!("Hello Solana! (from Rust!)");


    // Iterating accounts is safer than indexing
    let accounts_iter = &mut accounts.iter();

    // Get the account to say hello to
    let account = next_account_info(accounts_iter)?;

    // The account must be owned by the program in order to modify its data
    if account.owner != program_id {
        msg!("Greeted account does not have the correct program id");
        return Err(ProgramError::IncorrectProgramId);
    }


    let mut calculator = Calculator::try_from_slice(&account.data.borrow())?;

    let calculator_instructions = CalculatorInstructions::try_from_slice(&instruction_data)?;
    msg!("Current value before evaluation: {}", calculator.value);
    
    calculator.value = calculator_instructions.evaluate(calculator.value);
    calculator.serialize(&mut &mut account.data.borrow_mut()[..])?;

    msg!("Current value after evaluation: {}", calculator.value);



    Ok(())
}
