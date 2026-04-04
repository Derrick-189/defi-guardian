// Simple Rust contract for testing DeFi Guardian verification
// This demonstrates basic state management and invariants

#[derive(Debug)]
pub struct SimpleContract {
    pub balance: u64,
    pub owner: String,
    pub locked: bool,
}

impl SimpleContract {
    pub fn new(owner: String) -> Self {
        SimpleContract {
            balance: 0,
            owner,
            locked: false,
        }
    }

    pub fn deposit(&mut self, amount: u64) {
        assert!(!self.locked, "Contract is locked");
        assert!(amount > 0, "Amount must be positive");

        self.balance += amount;
        assert!(self.balance >= amount, "Balance overflow detected");
    }

    pub fn withdraw(&mut self, amount: u64) -> Result<(), &'static str> {
        if self.locked {
            return Err("Contract is locked");
        }
        if amount > self.balance {
            return Err("Insufficient balance");
        }

        self.balance -= amount;
        Ok(())
    }

    pub fn lock(&mut self) {
        self.locked = true;
    }

    pub fn unlock(&mut self) {
        self.locked = false;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deposit() {
        let mut contract = SimpleContract::new("owner".to_string());
        contract.deposit(100);
        assert_eq!(contract.balance, 100);
    }

    #[test]
    fn test_withdraw() {
        let mut contract = SimpleContract::new("owner".to_string());
        contract.deposit(100);
        assert!(contract.withdraw(50).is_ok());
        assert_eq!(contract.balance, 50);
    }
}